# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from typing import Literal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, random_string

from mail.agent import create_dkim_key_on_agents, delete_dkim_key_from_agents
from mail.mail.doctype.dns_record.dns_record import create_or_update_dns_record
from mail.utils import get_dkim_host


class DKIMKey(Document):
	def autoname(self) -> None:
		self.name = f"{self.domain_name.replace('.', '-')}-{random_string(length=10)}"

	def validate(self) -> None:
		self.validate_rsa_key_size()

		if self.is_new():
			self.generate_dkim_keys()

	def on_update(self) -> None:
		if self.enabled:
			if self.has_value_changed("enabled"):
				self.create_or_update_dns_record()
				self.disable_existing_dkim_keys()
				create_dkim_key_on_agents(self.domain_name, self.rsa_private_key)
		elif self.has_value_changed("enabled"):
			delete_dkim_key_from_agents(self.domain_name)

	def on_trash(self) -> None:
		if frappe.session.user != "Administrator":
			frappe.throw(_("Only Administrator can delete DKIM Key."))

		if self.enabled:
			delete_dkim_key_from_agents(self.domain_name)

	def validate_rsa_key_size(self) -> None:
		"""Validates the Key Size."""

		if not self.rsa_key_size:
			self.rsa_key_size = frappe.db.get_single_value(
				"Mail Settings", "default_dkim_rsa_key_size", cache=True
			)

	def generate_dkim_keys(self) -> None:
		"""Generates the DKIM Keys."""

		self.rsa_private_key, self.rsa_public_key = generate_dkim_keys("rsa-sha256", cint(self.rsa_key_size))

	def create_or_update_dns_record(self) -> None:
		"""Creates or Updates the DNS Record."""

		create_or_update_dns_record(
			host=f"{get_dkim_host(self.domain_name, 'rsa')}._domainkey",
			type="TXT",
			value=f"v=DKIM1; k=rsa; h=sha256; p={self.rsa_public_key}",
			ttl=300,
			category="Sending Record",
			attached_to_doctype=self.doctype,
			attached_to_docname=self.name,
		)

	def disable_existing_dkim_keys(self) -> None:
		"""Disables the existing DKIM Keys."""

		filters = {"enabled": 1, "domain_name": self.domain_name, "name": ["!=", self.name]}
		for dkim_key in frappe.db.get_all("DKIM Key", filters, pluck="name"):
			dkim_key = frappe.get_doc("DKIM Key", dkim_key)
			dkim_key.enabled = 0
			dkim_key.save(ignore_permissions=True)


def create_dkim_key(domain_name: str, rsa_key_size: int | None = None) -> "DKIMKey":
	"""Creates a DKIM Key document."""

	doc = frappe.new_doc("DKIM Key")
	doc.enabled = 1
	doc.domain_name = domain_name
	doc.rsa_key_size = rsa_key_size
	doc.flags.ignore_links = True
	doc.save(ignore_permissions=True)

	return doc


def get_dkim_private_key(domain_name: str, raise_exception: bool = True) -> str | None:
	"""Returns the DKIM private key for the given domain."""

	private_key = frappe.db.get_value(
		"DKIM Key", {"enabled": 1, "domain_name": domain_name}, "rsa_private_key"
	)
	if not private_key and raise_exception:
		frappe.throw(_("DKIM Key not found for the domain {0}").format(frappe.bold(domain_name)))

	return private_key


def generate_dkim_keys(
	algorithm: Literal["rsa-sha256", "ed25519-sha256"], rsa_key_size: int = 2048
) -> tuple[str, str]:
	"""Generates the DKIM Keys for the specified algorithm."""

	def get_filtered_dkim_key(key_pem: str) -> str:
		"""Returns the filtered DKIM Key."""

		key_pem = "".join(key_pem.split())
		key_pem = (
			key_pem.replace("-----BEGINPUBLICKEY-----", "")
			.replace("-----ENDPUBLICKEY-----", "")
			.replace("-----BEGINRSAPRIVATEKEY-----", "")
			.replace("-----ENDRSAPRIVATEKEY-----", "")
			.replace("-----BEGINPRIVATEKEY-----", "")
			.replace("-----ENDPRIVATEKEY-----", "")
		)

		return key_pem

	from cryptography.hazmat.primitives import serialization

	if algorithm == "rsa-sha256":
		from cryptography.hazmat.backends import default_backend
		from cryptography.hazmat.primitives.asymmetric import rsa

		private_key = rsa.generate_private_key(
			public_exponent=65537, key_size=rsa_key_size, backend=default_backend()
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

		return private_key_pem, get_filtered_dkim_key(public_key_pem)

	elif algorithm == "ed25519-sha256":
		import base64

		from cryptography.hazmat.primitives.asymmetric import ed25519

		private_key = ed25519.Ed25519PrivateKey.generate()
		public_key = private_key.public_key()

		private_key_pem = private_key.private_bytes(
			encoding=serialization.Encoding.PEM,
			format=serialization.PrivateFormat.PKCS8,
			encryption_algorithm=serialization.NoEncryption(),
		).decode()
		public_key_raw = public_key.public_bytes(
			encoding=serialization.Encoding.Raw,
			format=serialization.PublicFormat.Raw,
		)
		public_key_encoded = base64.b64encode(public_key_raw).decode()

		return private_key_pem, public_key_encoded

	else:
		frappe.throw(_("Unsupported algorithm. Use 'rsa-sha256' or 'ed25519-sha256'."))
