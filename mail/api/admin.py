from typing import TYPE_CHECKING

import frappe

if TYPE_CHECKING:
	from mail.mail.doctype.mail_domain_request.mail_domain_request import MailDomainRequest


@frappe.whitelist()
def create_tenant(tenant_name: str) -> None:
	"""Create a new Mail Tenant"""

	tenant = frappe.new_doc("Mail Tenant")
	tenant.tenant_name = tenant_name
	tenant.user = frappe.session.user
	tenant.save(ignore_permissions=True)


@frappe.whitelist()
def create_domain_request(domain_name, mail_tenant) -> "MailDomainRequest":
	"""Create a new Mail Domain Request"""

	domain_request = frappe.new_doc("Mail Domain Request")
	domain_request.domain_name = domain_name
	domain_request.tenant = mail_tenant
	domain_request.user = frappe.session.user
	domain_request.insert()

	return domain_request


@frappe.whitelist()
def verify_dns_record(domain_request: str) -> bool:
	"""Verify the domain request key"""

	doc = frappe.get_doc("Mail Domain Request", domain_request)
	return doc.verify_and_create_domain(save=True)
