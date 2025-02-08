import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from mail.mail.doctype.mail_account.mail_account import create_user


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def self_signup(email: str) -> str:
	"""Create a new Mail Account Request for self signup"""

	account_request = frappe.new_doc("Mail Account Request")
	account_request.email = email
	account_request.is_admin = 1
	account_request.send_invite = 1
	account_request.insert(ignore_permissions=True)

	return account_request.name


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def resend_otp(account_request: str) -> None:
	"""Resend OTP to the user"""

	account_request = frappe.get_doc("Mail Account Request", account_request)
	account_request.set_otp()
	account_request.save(ignore_permissions=True)
	account_request.send_verification_email()


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def verify_otp(account_request: str, otp: str) -> str:
	"""Verify the OTP and return the request key"""

	actual_otp, request_key = frappe.db.get_value(
		"Mail Account Request", account_request, ["otp", "request_key"]
	)
	if otp != actual_otp:
		frappe.throw(_("Invalid OTP. Please try again."))

	return request_key


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def get_account_request(request_key: str) -> dict:
	"""Return the account request details"""

	return frappe.db.get_value(
		"Mail Account Request",
		{"request_key": request_key},
		["email", "is_verified", "is_expired", "account"],
		as_dict=True,
	)


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=20, seconds=60)
def create_account(request_key: str, first_name: str, last_name: str, password: str) -> None:
	"""Create a new user account"""

	account_request = frappe.get_last_doc("Mail Account Request", {"request_key": request_key})
	account_request.validate_expired()
	account_request.is_verified = 1
	account_request.save(ignore_permissions=True)

	if account_request.account:
		account_request.create_account(first_name, last_name, password)

	else:
		create_user(account_request.email, first_name, last_name, password, ["Mail Admin"])
