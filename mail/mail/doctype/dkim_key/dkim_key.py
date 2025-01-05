# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _, generate_hash
from frappe.model.document import Document
from frappe.utils import cint
from frappe.utils.caching import request_cache

from mail.mail.doctype.dns_record.dns_record import create_or_update_dns_record


class DKIMKey(Document):
	def autoname(self) -> None:
		self.name = f"{self.domain_name.replace('.', '-')}-{generate_hash(length=10)}"

	def validate(self) -> None:
		self.validate_domain_name()
		self.validate_key_size()
		self.generate_dkim_keys()

	def after_insert(self) -> None:
		self.create_or_update_dns_record()
		self.disable_existing_dkim_keys()

	def on_trash(self) -> None:
		if frappe.session.user != "Administrator":
			frappe.throw(_("Only Administrator can delete DKIM Key."))

	def validate_domain_name(self) -> None:
		"""Validates the Domain Name."""

		if not self.domain_name:
			frappe.throw(_("Domain Name is mandatory"))

	def validate_key_size(self) -> None:
		"""Validates the Key Size."""

		if self.key_size:
			if cint(self.key_size) < 1024:
				frappe.throw(_("Key Size must be greater than 1024."))
		else:
			self.key_size = frappe.db.get_single_value("Mail Settings", "default_dkim_key_size", cache=True)

	def generate_dkim_keys(self) -> None:
		"""Generates the DKIM Keys."""

		self.private_key, self.public_key = generate_dkim_keys(cint(self.key_size))

	def create_or_update_dns_record(self) -> None:
		"""Creates or Updates the DNS Record."""

		frappe.flags.enqueue_dns_record_update = True
		create_or_update_dns_record(
			host=f"{self.domain_name.replace('.', '-')}._domainkey",
			type="TXT",
			value=f"v=DKIM1; k=rsa; p={self.public_key}",
			ttl=300,
			category="Sending Record",
			attached_to_doctype=self.doctype,
			attached_to_docname=self.name,
		)

	def disable_existing_dkim_keys(self) -> None:
		"""Disables the existing DKIM Keys."""

		DKIM_KEY = frappe.qb.DocType("DKIM Key")
		(
			frappe.qb.update(DKIM_KEY)
			.set(DKIM_KEY.enabled, 0)
			.where(
				(DKIM_KEY.enabled == 1)
				& (DKIM_KEY.name != self.name)
				& (DKIM_KEY.domain_name == self.domain_name)
			)
		).run()


def create_dkim_key(domain_name: str, key_size: int | None = None) -> "DKIMKey":
	"""Creates a DKIM Key document."""

	doc = frappe.new_doc("DKIM Key")
	doc.enabled = 1
	doc.domain_name = domain_name
	doc.key_size = key_size
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)

	return doc


@request_cache
def get_dkim_private_key(domain_name: str, raise_exception: bool = True) -> str | None:
	"""Returns the DKIM private key for the given domain."""

	private_key = frappe.db.get_value("DKIM Key", {"enabled": 1, "domain_name": domain_name}, "private_key")

	if not private_key and raise_exception:
		frappe.throw(_("DKIM Key not found for the domain {0}").format(frappe.bold(domain_name)))

	return private_key


def generate_dkim_keys(key_size: int = 1024) -> tuple[str, str]:
	"""Generates the DKIM Keys."""

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
