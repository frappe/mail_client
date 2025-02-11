import frappe
from frappe import _

from mail.mail.doctype.ip_blacklist.ip_blacklist import get_blacklist_for_ip_address
from mail.utils.rate_limiter import dynamic_rate_limit


@frappe.whitelist(methods=["GET"], allow_guest=True)
@dynamic_rate_limit()
def get(ip_address: str) -> dict:
	"""Returns the blacklist for the given IP address."""

	if not ip_address:
		frappe.throw(_("IP address is required."), frappe.MandatoryError)

	return get_blacklist_for_ip_address(ip_address, create_if_not_exists=True, commit=True) or {}
