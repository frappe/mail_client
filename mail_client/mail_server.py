from typing import Any
from urllib.parse import urljoin

import frappe
from frappe.frappeclient import FrappeClient, FrappeOAuth2Client
from frappe.utils import convert_utc_to_system_timezone, get_datetime


class MailServerAPI:
	"""Class to interact with the Frappe Mail Server."""

	def __init__(
		self,
		server: str,
		api_key: str | None = None,
		api_secret: str | None = None,
		access_token: str | None = None,
	) -> None:
		self.server = server
		self.api_key = api_key
		self.api_secret = api_secret
		self.access_token = access_token
		self.client = self.get_client(self.server, self.api_key, self.api_secret, self.access_token)

	@staticmethod
	def get_client(
		server: str,
		api_key: str | None = None,
		api_secret: str | None = None,
		access_token: str | None = None,
	) -> FrappeClient | FrappeOAuth2Client:
		"""Returns a FrappeClient or FrappeOAuth2Client instance."""

		if hasattr(frappe.local, "frappe_mail_server"):
			return frappe.local.frappe_mail_server

		client = (
			FrappeOAuth2Client(url=server, access_token=access_token)
			if access_token
			else FrappeClient(url=server, api_key=api_key, api_secret=api_secret)
		)
		frappe.local.frappe_mail_server = client

		return client

	def request(
		self,
		method: str,
		endpoint: str,
		params: dict | None = None,
		data: dict | None = None,
		json: dict | None = None,
		headers: dict[str, str] | None = None,
		timeout: int | tuple[int, int] = (60, 120),
	) -> Any | None:
		"""Makes an HTTP request to the Frappe Mail Server."""

		url = urljoin(self.client.url, endpoint)

		headers = headers or {}
		headers.update(self.client.headers)

		response = self.client.session.request(
			method=method,
			url=url,
			params=params,
			data=data,
			json=json,
			headers=headers,
			timeout=timeout,
		)

		return self.client.post_process(response)


class MailServerAuthAPI(MailServerAPI):
	"""Class to authenticate with the Frappe Mail Server."""

	def validate(self) -> None:
		"""Validates the API key and secret with the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.auth.validate"
		self.request("POST", endpoint=endpoint)


class MailServerDomainAPI(MailServerAPI):
	"""Class to manage domains in the Frappe Mail Server."""

	def add_or_update_domain(self, domain_name: str, mail_client_host: str | None = None) -> dict:
		"""Adds or updates a domain in the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.domain.add_or_update_domain"
		data = {"domain_name": domain_name, "mail_client_host": mail_client_host}
		return self.request("POST", endpoint=endpoint, data=data)

	def get_dns_records(self, domain_name: str) -> list[dict] | None:
		"""Returns the DNS records for a domain from the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.domain.get_dns_records"
		params = {"domain_name": domain_name}
		return self.request("GET", endpoint=endpoint, params=params)

	def verify_dns_records(self, domain_name: str) -> list[str] | None:
		"""Verifies the DNS records for a domain in the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.domain.verify_dns_records"
		data = {"domain_name": domain_name}
		return self.request("POST", endpoint=endpoint, data=data)


class MailServerOutboundAPI(MailServerAPI):
	"""Class to send outbound emails using the Frappe Mail Server."""

	def send(self, outgoing_mail: str, recipients: str | list[str], message: str) -> str:
		"""Sends an email message to the recipients using the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.outbound.send"
		data = {
			"outgoing_mail": outgoing_mail,
			"recipients": recipients,
			"message": message,
		}
		return self.request("POST", endpoint=endpoint, json=data)

	def fetch_delivery_status(self, outgoing_mail: str, token: str) -> dict:
		"""Fetches the delivery status of an email from the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.outbound.fetch_delivery_status"
		data = {"outgoing_mail": outgoing_mail, "token": token}
		return self.request("GET", endpoint=endpoint, data=data)

	def fetch_delivery_statuses(self, data: list[dict]) -> list[dict]:
		"""Fetches the delivery statuses of emails from the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.outbound.fetch_delivery_statuses"
		return self.request("GET", endpoint=endpoint, json={"data": data})


class MailServerInboundAPI(MailServerAPI):
	"""Class to receive inbound emails from the Frappe Mail Server."""

	def fetch(self, limit: int = 100, last_synced_at: str | None = None) -> dict[str, list[dict] | str]:
		"""Fetches inbound emails from the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.inbound.fetch"
		data = {"limit": limit, "last_synced_at": last_synced_at}
		result = self.request("GET", endpoint=endpoint, data=data)
		result["last_synced_at"] = convert_utc_to_system_timezone(get_datetime(result["last_synced_at"]))

		return result


def get_mail_server_api() -> "MailServerAPI":
	"""Returns a MailServerAPI instance."""

	client_settings = frappe.get_cached_doc("Mail Client Settings")
	return MailServerAPI(
		client_settings.mail_server_host,
		client_settings.mail_server_api_key,
		client_settings.get_password("mail_server_api_secret"),
	)


def get_mail_server_auth_api() -> "MailServerAuthAPI":
	"""Returns a MailServerAuthAPI instance."""

	client_settings = frappe.get_cached_doc("Mail Client Settings")
	return MailServerAuthAPI(
		client_settings.mail_server_host,
		client_settings.mail_server_api_key,
		client_settings.get_password("mail_server_api_secret"),
	)


def get_mail_server_domain_api() -> "MailServerDomainAPI":
	"""Returns a MailServerDomainAPI instance."""

	client_settings = frappe.get_cached_doc("Mail Client Settings")
	return MailServerDomainAPI(
		client_settings.mail_server_host,
		client_settings.mail_server_api_key,
		client_settings.get_password("mail_server_api_secret"),
	)


def get_mail_server_outbound_api() -> "MailServerOutboundAPI":
	"""Returns a MailServerOutboundAPI instance."""

	client_settings = frappe.get_cached_doc("Mail Client Settings")
	return MailServerOutboundAPI(
		client_settings.mail_server_host,
		client_settings.mail_server_api_key,
		client_settings.get_password("mail_server_api_secret"),
	)


def get_mail_server_inbound_api() -> "MailServerInboundAPI":
	"""Returns a MailServerInboundAPI instance."""

	client_settings = frappe.get_cached_doc("Mail Client Settings")
	return MailServerInboundAPI(
		client_settings.mail_server_host,
		client_settings.mail_server_api_key,
		client_settings.get_password("mail_server_api_secret"),
	)
