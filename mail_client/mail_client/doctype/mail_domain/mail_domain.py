# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail_client.mail_client.doctype.mailbox.mailbox import create_postmaster_mailbox
from mail_client.mail_server import get_mail_server_domain_api


class MailDomain(Document):
	def autoname(self) -> None:
		self.domain_name = self.domain_name.strip().lower()
		self.name = self.domain_name

	def validate(self) -> None:
		self.validate_newsletter_retention()

		if self.is_new():
			self.validate_duplicate()
			self.access_token = generate_access_token()
			self.dkim_private_key, self.dkim_public_key = generate_dkim_keys()
			self.add_or_update_domain_in_mail_server()
			self.refresh_dns_records(do_not_save=True)

		if not self.enabled:
			self.is_verified = 0

	def after_insert(self) -> None:
		create_postmaster_mailbox(self.domain_name)

	def validate_newsletter_retention(self) -> None:
		"""Validates the Newsletter Retention."""

		if self.newsletter_retention:
			if self.newsletter_retention < 1:
				frappe.throw(_("Newsletter Retention must be greater than 0."))

			max_newsletter_retention = frappe.db.get_single_value(
				"Mail Client Settings", "max_newsletter_retention", cache=True
			)
			if self.newsletter_retention > max_newsletter_retention:
				frappe.throw(
					_("Newsletter Retention must be less than or equal to {0}.").format(
						frappe.bold(max_newsletter_retention)
					)
				)
		else:
			self.newsletter_retention = frappe.db.get_single_value(
				"Mail Client Settings", "default_newsletter_retention", cache=True
			)

	def validate_duplicate(self) -> None:
		"""Validate if the Mail Domain already exists."""

		if frappe.db.exists("Mail Domain", {"domain_name": self.domain_name}):
			frappe.throw(_("Mail Domain {0} already exists.").format(frappe.bold(self.domain_name)))

	def add_or_update_domain_in_mail_server(self) -> None:
		"""Adds or Updates the Domain in the Mail Server."""

		domain_api = get_mail_server_domain_api()
		domain_api.add_or_update_domain(
			domain_name=self.domain_name,
			access_token=self.access_token,
			dkim_public_key=self.dkim_public_key,
			mail_client_host=frappe.utils.get_url(),
		)

	@frappe.whitelist()
	def refresh_dns_records(self, do_not_save: bool = False) -> None:
		"""Refreshes the DNS Records."""

		self.is_verified = 0
		self.dns_records.clear()

		domain_api = get_mail_server_domain_api()
		dns_records = domain_api.get_dns_records(self.domain_name)

		for record in dns_records:
			self.append("dns_records", record)

		if not do_not_save:
			self.save()

	@frappe.whitelist()
	def verify_dns_records(self, do_not_save: bool = False) -> None:
		"""Verifies the DNS Records."""

		domain_api = get_mail_server_domain_api()
		errors = domain_api.verify_dns_records(self.domain_name)

		if not errors:
			self.is_verified = 1
			frappe.msgprint(_("DNS Records verified successfully."), indicator="green", alert=True)
		else:
			self.is_verified = 0
			frappe.msgprint(errors, title="DNS Verification Failed", indicator="red", as_list=True)

		if not do_not_save:
			self.save()

	@frappe.whitelist()
	def rotate_dkim_keys(self) -> None:
		"""Rotates the DKIM Keys."""

		frappe.only_for(["System Manager", "Administrator"])
		self.dkim_private_key, self.dkim_public_key = generate_dkim_keys()
		self.add_or_update_domain_in_mail_server()
		self.save()
		frappe.msgprint(_("DKIM Keys rotated successfully."), indicator="green", alert=True)

	@frappe.whitelist()
	def rotate_access_token(self) -> None:
		"""Rotates the Access Token."""

		frappe.only_for(["System Manager", "Administrator"])
		self.access_token = generate_access_token()
		self.add_or_update_domain_in_mail_server()
		self.save()
		frappe.msgprint(_("Access Token rotated successfully."), indicator="green", alert=True)


def generate_access_token() -> str:
	"""Generates and returns the Access Token."""

	return frappe.generate_hash(length=32)


def generate_dkim_keys(key_size: int = 2048) -> tuple[str, str]:
	"""Generates and returns the DKIM Keys (Private and Public)."""

	def get_filtered_dkim_key(key_pem: str) -> str:
		"""Returns the filtered DKIM Key."""

		key_pem = "".join(key_pem.split())
		key_pem = (
			key_pem.replace("-----BEGINPUBLICKEY-----", "")
			.replace("-----ENDPUBLICKEY-----", "")
			.replace("-----BEGINRSAPRIVATEKEY-----", "")
			.replace("----ENDRSAPRIVATEKEY-----", "")
		)

		return key_pem

	from cryptography.hazmat.backends import default_backend
	from cryptography.hazmat.primitives import serialization
	from cryptography.hazmat.primitives.asymmetric import rsa

	private_key = rsa.generate_private_key(
		public_exponent=65537, key_size=key_size, backend=default_backend()
	)
	public_key = private_key.public_key()

	private_key_pem = private_key.private_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.TraditionalOpenSSL,
		encryption_algorithm=serialization.NoEncryption(),
	).decode()
	public_key_pem = public_key.public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo,
	).decode()

	private_key = private_key_pem
	public_key = get_filtered_dkim_key(public_key_pem)

	return private_key, public_key
