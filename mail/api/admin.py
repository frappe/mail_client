from typing import TYPE_CHECKING

import frappe
from frappe import _
from frappe.utils import validate_email_address

from mail.utils.user import is_tenant_admin

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
def get_domain_request(domain_name: str, mail_tenant: str) -> "MailDomainRequest":
	"""Fetches Mail Domain Request for a given domain name if it exists, and creates a new one if not"""

	if frappe.db.exists("Mail Domain", domain_name):
		frappe.throw(_("Domain {0} has already been registered.").format(domain_name))

	if name := frappe.db.exists("Mail Domain Request", {"domain_name": domain_name, "tenant": mail_tenant}):
		return frappe.get_doc("Mail Domain Request", name)

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


@frappe.whitelist()
def get_tenant_members(tenant: str) -> list:
	"""Returns list of members for the given tenant"""

	user = frappe.session.user
	if not is_tenant_admin(tenant, user):
		frappe.throw(_("User {0} is not a Mail Admin of Tenant {1}.").format(user, tenant))

	MTM = frappe.qb.DocType("Mail Tenant Member")
	User = frappe.qb.DocType("User")

	return (
		frappe.qb.from_(MTM)
		.left_join(User)
		.on(MTM.user == User.name)
		.select(User.name, User.full_name, User.user_image, MTM.is_admin)
		.where(MTM.tenant == tenant)
		.orderby(MTM.creation)
	).run(as_dict=True)


@frappe.whitelist()
def add_member(
	tenant: str,
	username: str,
	domain: str,
	role: str,
	send_invite: bool,
	email: str | None = None,
	first_name: str | None = None,
	last_name: str | None = None,
	password: str | None = None,
) -> None:
	"""Create a new Mail Account Request for adding a member"""

	account_request = frappe.new_doc("Mail Account Request")
	account_request.is_invite = 1
	account_request.tenant = tenant
	account_request.domain_name = domain
	account_request.account = f"{username}@{domain}"
	account_request.role = role
	account_request.invited_by = frappe.session.user
	account_request.email = email
	account_request.send_email = send_invite
	account_request.insert()

	if not send_invite:
		account_request.force_verify_and_create_account(first_name, last_name, password)
