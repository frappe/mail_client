# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.utils.dns import get_dns_record


class MailAgentGroup(Document):
	def autoname(self) -> None:
		self.agent_group = self.agent_group.lower()
		self.name = self.agent_group

	def validate(self) -> None:
		self.validate_enabled()
		self.validate_agent_group()
		self.validate_priority()

	def validate_enabled(self) -> None:
		"""Validates the enabled status of the agent group."""

		if self.enabled and not self.inbound and not self.outbound:
			self.enabled = 0

	def validate_agent_group(self) -> None:
		"""Validates the agent group and fetches the IP addresses."""

		if self.is_new() and frappe.db.exists("Mail Agent Group", self.agent_group):
			frappe.throw(_("Mail Agent Group {0} already exists.").format(frappe.bold(self.agent_group)))

		self.ipv4_addresses = "\n".join([r.address for r in get_dns_record(self.agent_group, "A") or []])
		self.ipv6_addresses = "\n".join([r.address for r in get_dns_record(self.agent_group, "AAAA") or []])

	def validate_priority(self) -> None:
		"""Validates the priority of the agent group."""

		if frappe.db.exists(
			"Mail Agent Group",
			{"enabled": 1, "inbound": 1, "priority": self.priority, "name": ["!=", self.name]},
		):
			frappe.throw(
				_("Mail Agent Group with priority {0} already exists.").format(frappe.bold(self.priority))
			)
