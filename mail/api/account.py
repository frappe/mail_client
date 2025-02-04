import frappe
from frappe import _
from frappe.utils import validate_email_address


@frappe.whitelist(allow_guest=True)
def self_signup(email: str) -> str:
	"""Create a new Mail Account Request for self signup"""

	email = email.strip().lower()
	validate_email_address(email, True)

	account_request = frappe.new_doc("Mail Account Request")
	account_request.email = email
	account_request.role = "Mail Admin"
	account_request.send_email = True
	account_request.insert(ignore_permissions=True)

	return account_request.name


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

	if send_invite:
		email = email.strip().lower()
		validate_email_address(email, True)
		account_request.email = email
		account_request.send_email = True

	account_request.insert()

	if not send_invite:
		account_request.force_verify_and_create_account(first_name, last_name, password)


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
