# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now
from frappe.model.document import Document


class DNSRecord(Document):
	def validate(self):
		if self.is_new():
			self.validate_ttl()

	def validate_ttl(self) -> None:
		"""Validates the TTL value"""

		if not self.ttl:
			self.ttl = frappe.db.get_single_value("Mail Settings", "default_ttl", cache=True)

	def get_fqdn(self) -> str:
		"""Returns the Fully Qualified Domain Name"""

		from mail.utils.cache import get_root_domain_name

		return f"{self.host}.{get_root_domain_name()}"

	@frappe.whitelist()
	def verify_dns_record(self, save: bool = False) -> None:
		"""Verifies the DNS Record"""

		from mail.utils import verify_dns_record

		self.is_verified = 0
		self.last_checked_at = now()
		if verify_dns_record(self.get_fqdn(), self.type, self.value):
			self.is_verified = 1
			frappe.msgprint(
				_("Verified {0}:{1} record.").format(
					frappe.bold(self.get_fqdn()), frappe.bold(self.type)
				),
				indicator="green",
				alert=True,
			)

		if save:
			self.save()


def create_or_update_dns_record(
	host: str,
	type: str,
	value: str,
	ttl: int | None = None,
	priority: int | None = None,
	category: str | None = None,
	attached_to_doctype: str | None = None,
	attached_to_docname: str | None = None,
) -> "DNSRecord":
	"""Creates or updates a DNS Record"""

	if dns_record := frappe.db.exists("DNS Record", {"host": host, "type": type}):
		dns_record = frappe.get_doc("DNS Record", dns_record)
	else:
		dns_record = frappe.new_doc("DNS Record")
		dns_record.host = host
		dns_record.type = type
		dns_record.attached_to_doctype = attached_to_doctype
		dns_record.attached_to_docname = attached_to_docname

	dns_record.value = value
	dns_record.ttl = ttl
	dns_record.priority = priority
	dns_record.category = category
	dns_record.save()

	return dns_record


def after_doctype_insert():
	frappe.db.add_unique("DNS Record", ["host", "type"])
