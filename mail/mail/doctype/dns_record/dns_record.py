# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, now

from mail.mail.doctype.dns_record.dns_provider import DNSProvider
from mail.utils.cache import get_root_domain_name
from mail.utils.dns import verify_dns_record


class DNSRecord(Document):
	def validate(self) -> None:
		if self.is_new():
			self.validate_duplicate_record()

		self.validate_ttl()

	def on_update(self) -> None:
		if self.has_value_changed("value") or self.has_value_changed("ttl"):
			if frappe.flags.do_not_enqueue:
				self.create_or_update_record_in_dns_provider()
				self.reload()
			else:
				frappe.enqueue_doc(
					self.doctype,
					self.name,
					"create_or_update_record_in_dns_provider",
					queue="short",
					enqueue_after_commit=True,
					at_front=True,
				)

	def on_trash(self) -> None:
		self.delete_record_from_dns_provider()

	def validate_duplicate_record(self) -> None:
		"""Validates if a duplicate DNS Record exists"""

		if frappe.db.exists(
			"DNS Record",
			{"host": self.host, "type": self.type, "name": ["!=", self.name]},
		):
			frappe.throw(
				_("DNS Record with the same host and type already exists."),
				title=_("Duplicate Record"),
			)

	def validate_ttl(self) -> None:
		"""Validates the TTL value"""

		if not self.ttl:
			self.ttl = frappe.db.get_single_value("Mail Settings", "default_ttl", cache=True)

	def create_or_update_record_in_dns_provider(self) -> None:
		"""Creates or Updates the DNS Record in the DNS Provider"""

		result = False
		mail_settings = frappe.get_single("Mail Settings")

		if mail_settings.dns_provider and mail_settings.dns_provider_token:
			dns_provider = DNSProvider(
				provider=mail_settings.dns_provider,
				token=mail_settings.get_password("dns_provider_token"),
			)
			result = dns_provider.create_or_update_dns_record(
				domain=mail_settings.root_domain_name,
				type=self.type,
				host=self.host,
				value=self.value,
				ttl=self.ttl,
				priority=self.priority,
			)

		self._db_set(is_verified=cint(result), last_checked_at=now(), notify_update=True)

	def delete_record_from_dns_provider(self) -> None:
		"""Deletes the DNS Record from the DNS Provider"""

		mail_settings = frappe.get_single("Mail Settings")

		if not mail_settings.dns_provider or not mail_settings.dns_provider_token:
			return

		dns_provider = DNSProvider(
			provider=mail_settings.dns_provider,
			token=mail_settings.get_password("dns_provider_token"),
		)
		dns_provider.delete_dns_record(domain=mail_settings.root_domain_name, type=self.type, host=self.host)

	def get_fqdn(self) -> str:
		"""Returns the Fully Qualified Domain Name"""

		return f"{self.host}.{get_root_domain_name()}"

	@frappe.whitelist()
	def verify_dns_record(self, save: bool = False) -> None:
		"""Verifies the DNS Record"""

		self.is_verified = 0
		self.last_checked_at = now()
		if verify_dns_record(self.get_fqdn(), self.type, self.value):
			self.is_verified = 1
			frappe.msgprint(
				_("Verified {0}:{1} record.").format(frappe.bold(self.get_fqdn()), frappe.bold(self.type)),
				indicator="green",
				alert=True,
			)
		else:
			frappe.msgprint(
				_("Could not verify {0}:{1} record.").format(
					frappe.bold(self.get_fqdn()), frappe.bold(self.type)
				),
				indicator="orange",
				alert=True,
			)

		if save:
			self.save()

	def _db_set(
		self,
		update_modified: bool = True,
		commit: bool = False,
		notify_update: bool = False,
		**kwargs,
	) -> None:
		"""Updates the document with the given key-value pairs."""

		self.db_set(kwargs, update_modified=update_modified, commit=commit)

		if notify_update:
			self.notify_update()


def create_or_update_dns_record(
	host: str,
	type: str,
	value: str,
	ttl: int | None = None,
	priority: int | None = None,
	category: str | None = None,
	attached_to_doctype: str | None = None,
	attached_to_docname: str | None = None,
	do_not_enqueue: bool = False,
) -> "DNSRecord":
	"""Creates or updates a DNS Record"""

	if do_not_enqueue:
		frappe.flags.do_not_enqueue = True

	if dns_record := frappe.db.exists("DNS Record", {"host": host, "type": type}):
		dns_record = frappe.get_doc("DNS Record", dns_record)
	else:
		dns_record = frappe.new_doc("DNS Record")
		dns_record.host = host
		dns_record.type = type

	dns_record.value = value
	dns_record.ttl = ttl
	dns_record.priority = priority
	dns_record.category = category
	dns_record.attached_to_doctype = attached_to_doctype
	dns_record.attached_to_docname = attached_to_docname
	dns_record.save(ignore_permissions=True)

	return dns_record


def verify_all_dns_records() -> None:
	"""Verifies all DNS Records"""

	dns_records = frappe.db.get_all("DNS Record", filters={}, pluck="name")
	for dns_record in dns_records:
		dns_record = frappe.get_doc("DNS Record", dns_record)
		dns_record.verify_dns_record(save=True)


def after_doctype_insert() -> None:
	frappe.db.add_unique("DNS Record", ["host", "type"])
