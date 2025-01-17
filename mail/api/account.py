import random

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def signup(email, referrer=None):
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
	new_otp = random.randint(10000, 99999)
	frappe.db.set_value("Mail Account Request", account_request, "otp", new_otp)
	print(new_otp)


@frappe.whitelist(allow_guest=True)
def verify_otp(account_request: str, otp: str):
	actual_otp, request_key = frappe.get_value(
		"Mail Account Request", account_request, ["otp", "request_key"]
	)
	if otp != actual_otp:
		frappe.throw("Invalid OTP. Please try again.")

	frappe.db.set_value("Mail Account Request", account_request, "otp", None)

	return request_key


@frappe.whitelist(allow_guest=True)
def get_verified_email(request_key: str):
	return frappe.get_value("Mail Account Request", {"request_key": request_key}, "email")


@frappe.whitelist(allow_guest=True)
def create_account(request_key: str, first_name, last_name, password):
	account_request, email, role = frappe.get_value(
		"Mail Account Request", {"request_key": request_key}, ["name", "email", "role"]
	)
	user = frappe.new_doc("User")
	user.first_name = first_name
	user.last_name = last_name
	user.email = email
	user.owner = email
	user.new_password = password
	user.append_roles(role)
	user.flags.no_welcome_mail = True
	user.save(ignore_permissions=True)

	frappe.db.set_value("Mail Account Request", account_request, "request_key", None)
