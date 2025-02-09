import frappe
from frappe import _
from frappe.rate_limiter import rate_limit

from mail.mail.doctype.ip_blacklist.ip_blacklist import get_blacklist_for_ip_address


@frappe.whitelist(methods=["GET"], allow_guest=True)
@rate_limit(limit=180, seconds=60 * 60)
def get(ip_address: str) -> dict:
	"""Returns the blacklist for the given IP address."""

	if not ip_address:
		frappe.throw(_("IP address is required."), frappe.MandatoryError)

	return get_blacklist_for_ip_address(ip_address, create_if_not_exists=True, commit=True) or {}
