# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from urllib.parse import quote

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, time_diff_in_seconds

from mail.agent import AgentAPI, Principal
from mail.utils import get_dkim_selector
from mail.utils.cache import get_primary_agents


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


def create_mail_agent_job(
	agent: str,
	method: str,
	endpoint: str,
	request_headers: dict | None = None,
	request_params: dict | None = None,
	request_data: str | None = None,
	request_json: dict | None = None,
) -> "MailAgentJob":
	"""Creates a new Mail Agent Job."""

	agent_job = frappe.new_doc("Mail Agent Job")
	agent_job.agent = agent
	agent_job.method = method
	agent_job.endpoint = endpoint
	agent_job.request_headers = request_headers
	agent_job.request_params = request_params
	agent_job.request_data = request_data
	agent_job.request_json = request_json
	agent_job.insert()

	return agent_job


def create_dkim_key_on_agents(
	domain_name: str, rsa_private_key: str, ed25519_private_key: str, agents: list[str] | None = None
) -> None:
	"""Creates a DKIM Key on all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	request_data = json.dumps(
		[
			{
				"type": "Insert",
				"prefix": f"signature.rsa-{domain_name}",
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
				"prefix": f"signature.ed25519-{domain_name}",
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
	for agent in primary_agents:
		create_mail_agent_job(
			agent=agent,
			method="POST",
			endpoint="/api/settings",
			request_data=request_data,
		)


def delete_dkim_key_from_agents(domain_name: str, agents: list[str] | None = None) -> None:
	"""Deletes a DKIM Key from all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	request_data = json.dumps(
		[
			{
				"type": "Clear",
				"prefix": f"signature.rsa-{domain_name}",
			},
			{
				"type": "Clear",
				"prefix": f"signature.ed25519-{domain_name}",
			},
		]
	)
	for agent in primary_agents:
		create_mail_agent_job(agent=agent, method="POST", endpoint="/api/settings", request_data=request_data)


def create_domain_on_agents(domain_name: str, agents: list[str] | None = None) -> None:
	"""Creates a domain on all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	principal = Principal(name=domain_name, type="domain").__dict__
	for agent in primary_agents:
		create_mail_agent_job(agent=agent, method="POST", endpoint="/api/principal", request_json=principal)


def delete_domain_from_agents(domain_name: str, agents: list[str] | None = None) -> None:
	"""Deletes a domain from all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	for agent in primary_agents:
		create_mail_agent_job(agent=agent, method="DELETE", endpoint=f"/api/principal/{domain_name}")


def create_account_on_agents(
	email: str, display_name: str, secret: str, agents: list[str] | None = None
) -> None:
	"""Creates an account on all primary agents."""

	primary_agents = agents or get_primary_agents()

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
		create_mail_agent_job(agent=agent, method="POST", endpoint="/api/principal", request_json=principal)


def patch_account_on_agents(
	email: str, display_name: str, new_secret: str, old_secret: str, agents: list[str] | None = None
) -> None:
	"""Patches an account on all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	request_data = [
		{
			"action": "set",
			"field": "description",
			"value": display_name,
		}
	]

	if old_secret != new_secret:
		request_data.extend(
			[
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

	request_data = json.dumps(request_data)
	for agent in primary_agents:
		create_mail_agent_job(
			agent=agent, method="PATCH", endpoint=f"/api/principal/{email}", request_data=request_data
		)


def delete_account_from_agents(email: str, agents: list[str] | None = None) -> None:
	"""Deletes an account from all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	for agent in primary_agents:
		create_mail_agent_job(agent=agent, method="DELETE", endpoint=f"/api/principal/{email}")


def create_group_on_agents(email: str, display_name: str, agents: list[str] | None = None) -> None:
	"""Creates a group on all primary agents."""

	primary_agents = agents or get_primary_agents()

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
		create_mail_agent_job(agent=agent, method="POST", endpoint="/api/principal", request_json=principal)


def patch_group_on_agents(email: str, display_name: str, agents: list[str] | None = None) -> None:
	"""Patches a group on all primary agents."""

	primary_agents = agents or get_primary_agents()

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
		create_mail_agent_job(
			agent=agent, method="PATCH", endpoint=f"/api/principal/{email}", request_data=request_data
		)


def delete_group_from_agents(email: str, agents: list[str] | None = None) -> None:
	"""Deletes a group from all primary agents."""

	delete_account_from_agents(email, agents)


def create_alias_on_agents(email: str, alias: str, agents: list[str] | None = None) -> None:
	"""Creates an alias on all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	request_data = json.dumps([{"action": "addItem", "field": "emails", "value": alias}])
	for agent in primary_agents:
		create_mail_agent_job(
			agent=agent, method="PATCH", endpoint=f"/api/principal/{email}", request_data=request_data
		)


def patch_alias_on_agents(
	new_email: str, old_email: str, alias: str, agents: list[str] | None = None
) -> None:
	"""Patches an alias on all primary agents."""

	delete_alias_from_agents(old_email, alias, agents)
	create_alias_on_agents(new_email, alias, agents)


def delete_alias_from_agents(email: str, alias: str, agents: list[str] | None = None) -> None:
	"""Deletes an alias from all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	request_data = json.dumps([{"action": "removeItem", "field": "emails", "value": alias}])
	for agent in primary_agents:
		create_mail_agent_job(
			agent=agent, method="PATCH", endpoint=f"/api/principal/{email}", request_data=request_data
		)


def create_member_on_agents(email: str, member: str, is_group: bool, agents: list[str] | None = None) -> None:
	"""Creates a group member on all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	endpoint = None
	request_data = None
	if is_group:
		endpoint = f"/api/principal/{member}"
		request_data = json.dumps([{"action": "addItem", "field": "memberOf", "value": email}])
	else:
		endpoint = f"/api/principal/{email}"
		request_data = json.dumps([{"action": "addItem", "field": "members", "value": member}])

	for agent in primary_agents:
		create_mail_agent_job(agent=agent, method="PATCH", endpoint=endpoint, request_data=request_data)


def patch_member_on_agents(
	new_email: str, old_email: str, member: str, is_group: bool, agents: list[str] | None = None
) -> None:
	"""Patches a group member on all primary agents."""

	delete_member_from_agents(old_email, member, is_group, agents)
	create_member_on_agents(new_email, member, is_group, agents)


def delete_member_from_agents(
	email: str, member: str, is_group: bool, agents: list[str] | None = None
) -> None:
	"""Deletes a group member from all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	endpoint = None
	request_data = None
	if is_group:
		endpoint = f"/api/principal/{member}"
		request_data = json.dumps([{"action": "removeItem", "field": "memberOf", "value": email}])
	else:
		endpoint = f"/api/principal/{email}"
		request_data = json.dumps([{"action": "removeItem", "field": "members", "value": member}])

	for agent in primary_agents:
		create_mail_agent_job(agent=agent, method="PATCH", endpoint=endpoint, request_data=request_data)
