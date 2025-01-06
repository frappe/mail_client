# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from urllib.parse import quote

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, time_diff_in_seconds

from mail.agent import AgentAPI, Principal
from mail.utils import get_dkim_host, get_dkim_selector


class MailAgentJob(Document):
	def validate(self) -> None:
		self.validate_agent()
		self.validate_endpoint()

	def after_insert(self) -> None:
		self.execute()

	def validate_agent(self) -> None:
		"""Validate if the agent is enabled."""
		if not frappe.get_cached_value("Mail Agent", self.agent, "enabled"):
			frappe.throw(_("Mail Agent {0} is disabled.").format(self.agent))

	def validate_endpoint(self) -> None:
		"""Validates the endpoint."""
		self.endpoint = quote(self.endpoint)

	def execute(self) -> None:
		"""Executes the job."""
		self.started_at = now()

		try:
			agent = frappe.get_cached_doc("Mail Agent", self.agent)

			if not agent.enabled:
				frappe.throw(_("Mail Agent {0} is disabled.").format(self.agent))

			agent_api = AgentAPI(
				agent.base_url,
				api_key=agent.get_password("api_key"),
				username=agent.username,
				password=agent.get_password("password"),
			)
			response = agent_api.request(
				method=self.method,
				endpoint=self.endpoint,
				params=self.request_params,
				data=self.request_data,
				json=self.request_json,
				headers=self.request_headers,
			)

			self.status = "Completed"
			if response.get("error"):
				self.status = "Failed"

			self.response_json = response
		except Exception:
			self.status = "Failed"
			self.error_log = frappe.get_traceback()
		finally:
			self.ended_at = now()
			self.duration = time_diff_in_seconds(self.ended_at, self.started_at)
			self.db_update()


def create_dkim_key_on_agents(
	domain_name: str, rsa_private_key: str, ed25519_private_key: str, agents: list[str] | None = None
) -> None:
	"""Creates a DKIM Key on all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "POST"
		agent_job.endpoint = "/api/settings"
		agent_job.request_data = json.dumps(
			[
				{
					"type": "Insert",
					"prefix": f"signature.{get_dkim_host(domain_name, 'rsa')}",
					"values": [
						["report", "true"],
						["selector", get_dkim_selector("rsa")],
						["canonicalization", "relaxed/relaxed"],
						["private-key", rsa_private_key],
						["algorithm", "rsa-sha256"],
						["domain", domain_name],
					],
					"assert_empty": True,
				},
				{
					"type": "Insert",
					"prefix": f"signature.{get_dkim_host(domain_name, 'ed25519')}",
					"values": [
						["report", "true"],
						["selector", get_dkim_selector("ed25519")],
						["canonicalization", "relaxed/relaxed"],
						["private-key", ed25519_private_key],
						["algorithm", "ed25519-sha256"],
						["domain", domain_name],
					],
					"assert_empty": True,
				},
			]
		)
		agent_job.insert()


def delete_dkim_key_from_agents(domain_name: str, agents: list[str] | None = None) -> None:
	"""Deletes a DKIM Key from all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "POST"
		agent_job.endpoint = "/api/settings"
		agent_job.request_data = json.dumps(
			[
				{
					"type": "Clear",
					"prefix": f"signature.{get_dkim_host(domain_name, 'rsa')}",
				},
				{
					"type": "Clear",
					"prefix": f"signature.{get_dkim_host(domain_name, 'ed25519')}",
				},
			]
		)
		agent_job.insert()


def create_domain_on_agents(domain_name: str, agents: list[str] | None = None) -> None:
	"""Creates a domain on all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	principal = Principal(name=domain_name, type="domain").__dict__
	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "POST"
		agent_job.endpoint = "/api/principal"
		agent_job.request_json = principal
		agent_job.insert()


def delete_domain_from_agents(domain_name: str, agents: list[str] | None = None) -> None:
	"""Deletes a domain from all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "DELETE"
		agent_job.endpoint = f"/api/principal/{domain_name}"
		agent_job.insert()


def create_account_on_agents(
	email: str, display_name: str, secret: str, agents: list[str] | None = None
) -> None:
	"""Creates an account on all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	principal = Principal(
		name=email,
		type="individual",
		description=display_name,
		secrets=[secret],
		emails=[email],
		roles=["user"],
	).__dict__
	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "POST"
		agent_job.endpoint = "/api/principal"
		agent_job.request_json = principal
		agent_job.insert()


def patch_account_on_agents(
	email: str, display_name: str, new_secret: str, old_secret: str, agents: list[str] | None = None
) -> None:
	"""Patches an account on all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	request_data = json.dumps(
		[
			{
				"action": "set",
				"field": "description",
				"value": display_name,
			},
			{
				"action": "addItem",
				"field": "secrets",
				"value": new_secret,
			},
			{
				"action": "removeItem",
				"field": "secrets",
				"value": old_secret,
			},
		]
	)
	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "PATCH"
		agent_job.endpoint = f"/api/principal/{email}"
		agent_job.request_data = request_data
		agent_job.insert()


def delete_account_from_agents(email: str, agents: list[str] | None = None) -> None:
	"""Deletes an account from all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "DELETE"
		agent_job.endpoint = f"/api/principal/{email}"
		agent_job.insert()


def create_group_on_agents(email: str, display_name: str, agents: list[str] | None = None) -> None:
	"""Creates a group on all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	principal = Principal(
		name=email,
		type="group",
		description=display_name,
		emails=[email],
		enabledPermissions=["email-send", "email-receive"],
	).__dict__
	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "POST"
		agent_job.endpoint = "/api/principal"
		agent_job.request_json = principal
		agent_job.insert()


def patch_group_on_agents(email: str, display_name: str, agents: list[str] | None = None) -> None:
	"""Patches a group on all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	request_data = json.dumps(
		[
			{
				"action": "set",
				"field": "description",
				"value": display_name,
			}
		]
	)
	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "PATCH"
		agent_job.endpoint = f"/api/principal/{email}"
		agent_job.request_data = request_data
		agent_job.insert()


def delete_group_from_agents(email: str, agents: list[str] | None = None) -> None:
	"""Deletes a group from all primary agents."""

	delete_account_from_agents(email, agents)


def create_alias_on_agents(account: str, alias: str, agents: list[str] | None = None) -> None:
	"""Creates an alias on all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	request_data = json.dumps([{"action": "addItem", "field": "emails", "value": alias}])
	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "PATCH"
		agent_job.endpoint = f"/api/principal/{account}"
		agent_job.request_data = request_data
		agent_job.insert()


def patch_alias_on_agents(
	new_account: str, old_account: str, alias: str, agents: list[str] | None = None
) -> None:
	"""Patches an alias on all primary agents."""

	delete_account_from_agents(old_account, alias, agents)
	create_alias_on_agents(new_account, alias, agents)


def delete_alias_from_agents(account: str, alias: str, agents: list[str] | None = None) -> None:
	"""Deletes an alias from all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	request_data = json.dumps([{"action": "removeItem", "field": "emails", "value": alias}])
	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "PATCH"
		agent_job.endpoint = f"/api/principal/{account}"
		agent_job.request_data = request_data
		agent_job.insert()


def create_member_on_agents(group: str, member: str, is_group: bool, agents: list[str] | None = None) -> None:
	"""Creates a group member on all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	endpoint = None
	request_data = None
	if is_group:
		endpoint = f"/api/principal/{member}"
		request_data = json.dumps([{"action": "addItem", "field": "memberOf", "value": group}])
	else:
		endpoint = f"/api/principal/{group}"
		request_data = json.dumps([{"action": "addItem", "field": "members", "value": member}])

	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "PATCH"
		agent_job.endpoint = endpoint
		agent_job.request_data = request_data
		agent_job.insert()


def patch_member_on_agents(
	new_group: str, old_group: str, member: str, is_group: bool, agents: list[str] | None = None
) -> None:
	"""Patches a group member on all primary agents."""

	delete_account_from_agents(old_group, member, is_group, agents)
	create_alias_on_agents(new_group, member, is_group, agents)


def delete_member_from_agents(
	group: str, member: str, is_group: bool, agents: list[str] | None = None
) -> None:
	"""Deletes a group member from all primary agents."""

	primary_agents = agents or frappe.db.get_all(
		"Mail Agent", filters={"enabled": 1, "is_primary": 1}, pluck="name"
	)

	if not primary_agents:
		return

	endpoint = None
	request_data = None
	if is_group:
		endpoint = f"/api/principal/{member}"
		request_data = json.dumps([{"action": "removeItem", "field": "memberOf", "value": group}])
	else:
		endpoint = f"/api/principal/{group}"
		request_data = json.dumps([{"action": "removeItem", "field": "members", "value": member}])

	for agent in primary_agents:
		agent_job = frappe.new_doc("Mail Agent Job")
		agent_job.agent = agent
		agent_job.method = "PATCH"
		agent_job.endpoint = endpoint
		agent_job.request_data = request_data
		agent_job.insert()
