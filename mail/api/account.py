import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from mail.mail.doctype.mail_account.mail_account import create_user
from mail.utils.rate_limiter import dynamic_rate_limit


@frappe.whitelist(allow_guest=True)
@dynamic_rate_limit()
def self_signup(email: str) -> str:
	"""Create a new Mail Account Request for self signup"""

	account_request = frappe.new_doc("Mail Account Request")
	account_request.email = email
	account_request.is_admin = 1
	account_request.send_invite = 1
	account_request.insert(ignore_permissions=True)

	return account_request.name


@frappe.whitelist(allow_guest=True)
@dynamic_rate_limit()
def resend_otp(account_request: str) -> None:
	"""Resend OTP to the user"""

	account_request = frappe.get_doc("Mail Account Request", account_request)
	account_request.set_otp()
	account_request.save(ignore_permissions=True)
	account_request.send_verification_email()


@frappe.whitelist(allow_guest=True)
@dynamic_rate_limit()
def verify_otp(account_request: str, otp: str) -> str:
	"""Verify the OTP and return the request key"""

	otp_hash = frappe.cache.get_value(f"account_request_otp_hash:{account_request}", expires=True)
	if not otp_hash or otp_hash != frappe.utils.sha256_hash(otp):
		frappe.throw(_("Invalid OTP. Please try again."))

	frappe.cache.delete_value(f"account_request_otp_hash:{account_request}")
	return frappe.db.get_value("Mail Account Request", account_request, "request_key")


@frappe.whitelist(allow_guest=True)
@dynamic_rate_limit()
def get_account_request(request_key: str) -> dict | None:
	"""Return the account request details"""

	if account_request := frappe.db.get_value(
		"Mail Account Request",
		{"request_key": request_key},
		["email", "is_verified", "expires_at", "account"],
		as_dict=True,
	):
		is_expired = 0
		if expires_at := account_request["expires_at"]:
			is_expired = cint(get_datetime(expires_at) < now_datetime())
		account_request.pop("expires_at")
		account_request["is_expired"] = is_expired
		return account_request


@frappe.whitelist(allow_guest=True)
@dynamic_rate_limit()
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
