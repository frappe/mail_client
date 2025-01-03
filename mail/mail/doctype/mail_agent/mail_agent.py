# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import base64

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import random_string

from mail.agent import AgentAPI, Principal
from mail.mail.doctype.dns_record.dns_record import create_or_update_dns_record
from mail.mail.doctype.mail_settings.mail_settings import (
	validate_mail_settings,
)
from mail.utils import generate_secret, get_dns_record


class MailAgent(Document):
	def autoname(self) -> None:
		self.agent = self.agent.lower()
		self.name = self.agent

	def validate(self) -> None:
		if self.is_new():
			validate_mail_settings()

		self.validate_agent()
		self.validate_agent_group()
		self.validate_is_primary()
		self.validate_api_key()

	def on_update(self) -> None:
		if self.has_value_changed("enabled") or self.has_value_changed("enable_outbound"):
			create_or_update_spf_dns_record()

	def on_trash(self) -> None:
		if frappe.session.user != "Administrator":
			frappe.throw(_("Only Administrator can delete Mail Agent."))

		if self.enable_outbound:
			self.db_set("enabled", 0)
			create_or_update_spf_dns_record()

	def validate_agent(self) -> None:
		"""Validates the agent and fetches the IP addresses."""

		if self.is_new() and frappe.db.exists("Mail Agent", self.agent):
			frappe.throw(_("Mail Agent {0} already exists.").format(frappe.bold(self.agent)))

		self.ipv4_addresses = "\n".join([r.address for r in get_dns_record(self.agent, "A") or []])
		self.ipv6_addresses = "\n".join([r.address for r in get_dns_record(self.agent, "AAAA") or []])

	def validate_agent_group(self) -> None:
		"""Validates the Mail Agent Group."""

		if not frappe.db.get_value("Mail Agent Group", self.agent_group, "enabled"):
			frappe.throw(_("Mail Agent Group {0} is disabled.").format(frappe.bold(self.agent_group)))

	def validate_is_primary(self) -> None:
		"""Validates the Is Primary field."""

		filters = {
			"is_primary": 1,
			"agent_group": self.agent_group,
			"name": ["!=", self.name],
		}

		if self.is_primary:
			frappe.db.set_value("Mail Agent", filters, "is_primary", 0)
		else:
			if not frappe.db.exists("Mail Agent", filters):
				self.is_primary = 1

	def validate_api_key(self) -> None:
		"""Validates the API Key or Username and Password."""

		if not self.api_key:
			if not self.username or not self.password:
				frappe.throw(_("API Key or Username and Password is required."))

			self.api_key = self.__generate_api_key()

	def __generate_api_key(self) -> str:
		"""Generates API Key for the given agent."""

		name = f"{random_string(10)}-{self.agent}".lower()
		secret = generate_secret()
		principal = Principal(
			name=name, type="apiKey", secrets=secret, roles=["admin"], enabledPermissions=["authenticate"]
		)
		agent_api = AgentAPI(self.base_url, username=self.username, password=self.get_password("password"))
		response = agent_api.request(method="POST", endpoint="/api/principal", json=principal.__dict__)

		if error := response.get("error"):
			frappe.throw(error)

		return f"api_{base64.b64encode(f'{name}:{secret}'.encode()).decode()}"


def create_or_update_spf_dns_record(spf_host: str | None = None) -> None:
	"""Refreshes the SPF DNS Record."""

	mail_settings = frappe.get_single("Mail Settings")
	spf_host = spf_host or mail_settings.spf_host
	outbound_agents = frappe.db.get_all(
		"Mail Agent",
		filters={"enabled": 1, "enable_outbound": 1},
		pluck="agent",
		order_by="agent asc",
	)

	if outbound_agents:
		outbound_agents = [f"a:{outbound_agent}" for outbound_agent in outbound_agents]
		create_or_update_dns_record(
			host=spf_host,
			type="TXT",
			value=f"v=spf1 {' '.join(outbound_agents)} ~all",
			ttl=mail_settings.default_ttl,
			category="Server Record",
		)
	else:
		if spf_dns_record := frappe.db.exists("DNS Record", {"host": spf_host, "type": "TXT"}):
			frappe.delete_doc("DNS Record", spf_dns_record, ignore_permissions=True)
