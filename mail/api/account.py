import random

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def signup(email):
	frappe.utils.validate_email_address(email, True)
	email = email.strip().lower()
	if frappe.db.exists("User", email):
		frappe.throw(_("User {0} is already registered").format(email))

	return frappe.get_doc(
		{
			"doctype": "Mail Account Request",
			"email": email,
			"role": "Mail Admin",
			"send_email": True,
		}
	).insert(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
def resend_otp(account_request: str):
	account_request = frappe.get_doc("Mail Account Request", account_request)
	account_request.otp = random.randint(10000, 99999)
	account_request.save(ignore_permissions=True)
	account_request.send_verification_email()


@frappe.whitelist(allow_guest=True)
def verify_otp(account_request: str, otp: str):
	actual_otp, request_key = frappe.db.get_value(
		"Mail Account Request", account_request, ["otp", "request_key"]
	)
	if otp != actual_otp:
		frappe.throw(_("Invalid OTP. Please try again."))

	return request_key


@frappe.whitelist(allow_guest=True)
def get_account_request(request_key: str):
	return frappe.db.get_value(
		"Mail Account Request",
		{"request_key": request_key},
		["email", "is_verified", "is_expired"],
		as_dict=True,
	)


@frappe.whitelist(allow_guest=True)
def create_account(request_key: str, first_name, last_name, password):
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
		mail_tenant.append("tenant_members", {"user": email})
		mail_tenant.save(ignore_permissions=True)
