import json
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urljoin

import frappe
import requests
from frappe import _

from mail.mail.doctype.mail_agent_request_log.mail_agent_request_log import (
	MailAgentRequestLog,
	create_mail_agent_request_log,
)
from mail.utils import get_dkim_selector
from mail.utils.cache import get_primary_agents


@dataclass
class Principal:
	"""Dataclass to represent a principal."""

	name: str
	type: Literal["domain", "apiKey", "individual"]
	id: int = 0
	quota: int = 0
	description: str = ""
	secrets: str | list[str] = field(default_factory=list)
	emails: list[str] = field(default_factory=list)
	urls: list[str] = field(default_factory=list)
	memberOf: list[str] = field(default_factory=list)
	roles: list[str] = field(default_factory=list)
	lists: list[str] = field(default_factory=list)
	members: list[str] = field(default_factory=list)
	enabledPermissions: list[str] = field(default_factory=list)
	disabledPermissions: list[str] = field(default_factory=list)
	externalMembers: list[str] = field(default_factory=list)


class AgentAPI:
	"""Class to interact with the Agent."""

	def __init__(
		self,
		base_url: str,
		api_key: str | None = None,
		username: str | None = None,
		password: str | None = None,
	) -> None:
		self.base_url = base_url
		self.__api_key = api_key
		self.__username = username
		self.__password = password
		self.__session = requests.Session()

		self.__auth = None
		self.__headers = {}
		if self.__api_key:
			self.__headers.update({"Authorization": f"Bearer {self.__api_key}"})
		else:
			if not self.__username or not self.__password:
				frappe.throw(_("API Key or Username and Password is required."))

			self.__auth = (self.__username, self.__password)

	def request(
		self,
		method: str,
		endpoint: str,
		params: dict | None = None,
		data: dict | None = None,
		json: dict | None = None,
		files: dict | None = None,
		headers: dict[str, str] | None = None,
		timeout: int | tuple[int, int] = (60, 120),
	) -> Any | None:
		"""Makes an HTTP request to the Agent."""

		url = urljoin(self.base_url, endpoint)

		headers = headers or {}
		headers.update(self.__headers)

		if files:
			headers.pop("content-type", None)

		response = self.__session.request(
			method=method,
			url=url,
			params=params,
			data=data,
			headers=headers,
			files=files,
			auth=self.__auth,
			timeout=timeout,
			json=json,
		)

		return response


def reload_configuration(agents: list[str] | None = None) -> None:
	"""Reloads the configuration on all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	for agent in primary_agents:
		create_mail_agent_request_log(
			agent=agent,
			method="GET",
			endpoint="/api/reload",
			do_not_enqueue=True,
		)


def reload_configuration_on_request_log_agent(request_log: MailAgentRequestLog):
	"""Reloads the configuration on the agent of the request log."""

	reload_configuration([request_log.agent])


def block_ip_on_agents(ip_address: str, agents: list[str] | None = None) -> None:
	"""Blocks an IP address on all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	request_data = json.dumps(
		[
			{
				"type": "insert",
				"prefix": None,
				"values": [[f"server.blocked-ip.{ip_address}", ""]],
				"assert_empty": True,
			}
		]
	)
	for agent in primary_agents:
		create_mail_agent_request_log(
			agent=agent,
			method="POST",
			endpoint="/api/settings",
			request_data=request_data,
			execute_on_end="mail.agent.reload_configuration_on_request_log_agent",
		)


def unblock_ip_on_agents(ip_address: str, agents: list[str] | None = None) -> None:
	"""Unblocks an IP address on all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	request_data = json.dumps([{"type": "delete", "keys": [f"server.blocked-ip.{ip_address}"]}])
	for agent in primary_agents:
		create_mail_agent_request_log(
			agent=agent,
			method="POST",
			endpoint="/api/settings",
			request_data=request_data,
			execute_on_end="mail.agent.reload_configuration_on_request_log_agent",
		)


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
				"type": "insert",
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
				"type": "insert",
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
		create_mail_agent_request_log(
			agent=agent,
			method="POST",
			endpoint="/api/settings",
			request_data=request_data,
			execute_on_end="mail.agent.reload_configuration_on_request_log_agent",
		)


def delete_dkim_key_from_agents(domain_name: str, agents: list[str] | None = None) -> None:
	"""Deletes a DKIM Key from all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	request_data = json.dumps(
		[
			{
				"type": "clear",
				"prefix": f"signature.rsa-{domain_name}",
			},
			{
				"type": "clear",
				"prefix": f"signature.ed25519-{domain_name}",
			},
		]
	)
	for agent in primary_agents:
		create_mail_agent_request_log(
			agent=agent,
			method="POST",
			endpoint="/api/settings",
			request_data=request_data,
			execute_on_end="mail.agent.reload_configuration_on_request_log_agent",
		)


def create_domain_on_agents(domain_name: str, agents: list[str] | None = None) -> None:
	"""Creates a domain on all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	principal = Principal(name=domain_name, type="domain").__dict__
	for agent in primary_agents:
		create_mail_agent_request_log(
			agent=agent, method="POST", endpoint="/api/principal", request_data=principal
		)


def delete_domain_from_agents(domain_name: str, agents: list[str] | None = None) -> None:
	"""Deletes a domain from all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	for agent in primary_agents:
		create_mail_agent_request_log(agent=agent, method="DELETE", endpoint=f"/api/principal/{domain_name}")


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
		create_mail_agent_request_log(
			agent=agent, method="POST", endpoint="/api/principal", request_data=principal
		)


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
		create_mail_agent_request_log(
			agent=agent, method="PATCH", endpoint=f"/api/principal/{email}", request_data=request_data
		)


def delete_account_from_agents(email: str, agents: list[str] | None = None) -> None:
	"""Deletes an account from all primary agents."""

	primary_agents = agents or get_primary_agents()

	if not primary_agents:
		return

	for agent in primary_agents:
		create_mail_agent_request_log(agent=agent, method="DELETE", endpoint=f"/api/principal/{email}")


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
		create_mail_agent_request_log(
			agent=agent, method="POST", endpoint="/api/principal", request_data=principal
		)


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
		create_mail_agent_request_log(
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
		create_mail_agent_request_log(
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
		create_mail_agent_request_log(
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
		create_mail_agent_request_log(
			agent=agent, method="PATCH", endpoint=endpoint, request_data=request_data
		)


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
		create_mail_agent_request_log(
			agent=agent, method="PATCH", endpoint=endpoint, request_data=request_data
		)
