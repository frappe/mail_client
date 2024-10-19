import frappe
from typing import Any
from urllib.parse import urljoin
from frappe.frappeclient import FrappeClient, FrappeOAuth2Client


class MailServer:
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
		self.client = self.get_client(
			self.server, self.api_key, self.api_secret, self.access_token
		)

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


class MailServerAuth(MailServer):
	"""Class to authenticate with the Frappe Mail Server."""

	def validate(self) -> None:
		"""Validates the API key and secret with the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.auth.validate"
		self.request("POST", endpoint=endpoint)


class MailServerDomain(MailServer):
	def add_or_update_domain(self, domain_name: str) -> dict:
		"""Adds or updates a domain in the Frappe Mail Server."""

		endpoint = "/api/method/mail_server.api.domain.add_or_update_domain"
		data = {"domain_name": domain_name}
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
