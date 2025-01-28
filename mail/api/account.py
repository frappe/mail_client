import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def signup(email) -> str:
	"""Create a new Mail Account Request"""

	email = email.strip().lower()
	frappe.utils.validate_email_address(email, True)

	if frappe.db.exists("User", email):
		frappe.throw(_("User {0} is already registered.").format(email))

	account_request = frappe.new_doc("Mail Account Request")
	account_request.email = email
	account_request.role = "Mail Admin"
	account_request.send_email = True
	account_request.insert(ignore_permissions=True)

	return account_request.name


@frappe.whitelist(allow_guest=True)
def resend_otp(account_request: str) -> None:
	"""Resend OTP to the user"""

	account_request = frappe.get_doc("Mail Account Request", account_request)
	account_request.set_otp()
	account_request.save(ignore_permissions=True)
	account_request.send_verification_email()


@frappe.whitelist(allow_guest=True)
def verify_otp(account_request: str, otp: str) -> str:
	"""Verify the OTP and return the request key"""

	actual_otp, request_key = frappe.db.get_value(
		"Mail Account Request", account_request, ["otp", "request_key"]
	)
	if otp != actual_otp:
		frappe.throw(_("Invalid OTP. Please try again."))

	return request_key


@frappe.whitelist(allow_guest=True)
def get_account_request(request_key: str) -> dict:
	"""Return the account request details"""

	return frappe.db.get_value(
		"Mail Account Request",
		{"request_key": request_key},
		["email", "is_verified", "is_expired"],
		as_dict=True,
	)


@frappe.whitelist(allow_guest=True)
def create_account(request_key: str, first_name: str, last_name: str, password: str) -> None:
	"""Create a new user account"""

	account_request, email, tenant, role = frappe.db.get_value(
		"Mail Account Request", {"request_key": request_key}, ["name", "email", "tenant", "role"]
	)

	user = frappe.new_doc("User")
	user.first_name = first_name
	user.last_name = last_name
	user.email = email
	user.owner = email
	user.new_password = password
	user.append_roles(role)
	user.flags.no_welcome_mail = True
	user.insert(ignore_permissions=True)

	frappe.db.set_value("Mail Account Request", account_request, "is_verified", 1)

	if tenant:
		mail_tenant = frappe.get_cached_doc("Mail Tenant", tenant)
		mail_tenant.add_member(email)


@frappe.whitelist()
def create_tenant(tenant_name: str) -> None:
	"""Create a new Mail Tenant"""

	tenant = frappe.new_doc("Mail Tenant")
	tenant.tenant_name = tenant_name
	tenant.user = frappe.session.user
	tenant.save(ignore_permissions=True)


@frappe.whitelist()
def create_domain_request(domain_name, mail_tenant) -> str:
	"""Create a new Mail Domain Request"""

	domain_request = frappe.new_doc("Mail Domain Request")
	domain_request.domain_name = domain_name
	domain_request.tenant = mail_tenant
	domain_request.user = frappe.session.user
	domain_request.insert()

	return domain_request.name


@frappe.whitelist()
def verify_domain_key(domain_request: str) -> bool:
	"""Verify the domain request key"""

	doc = frappe.get_doc("Mail Domain Request", domain_request)
	return doc.verify_and_create_domain(save=True)
