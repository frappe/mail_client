import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def signup(email, referrer=None):
	frappe.utils.validate_email_address(email, True)

	email = email.strip().lower()

	# exists, enabled = frappe.db.get_value("Mail Tenant", {"user": email}, ["name", "enabled"]) or [0, 0]

	# account_request = None
	# if exists and not enabled:
	# 	frappe.throw(_("Account {0} has been deactivated").format(email))
	# elif exists and enabled:
	# 	frappe.throw(_("Account {0} is already registered").format(email))

	return frappe.get_doc(
		{
			"doctype": "Mail Account Request",
			"email": email,
			"role": "Mail Admin",
			"send_email": True,
		}
	).insert(ignore_permissions=True)


@frappe.whitelist(allow_guest=True)
def verify_otp(account_request: str, otp: str):
	actual_otp, request_key = frappe.get_value(
		"Mail Account Request", account_request, ["otp", "request_key"]
	)
	if otp != actual_otp:
		frappe.throw("Invalid OTP. Please try again.")
	return request_key


@frappe.whitelist(allow_guest=True)
def get_verified_email(request_key: str):
	return frappe.get_value("Mail Account Request", {"request_key": request_key}, "email")
