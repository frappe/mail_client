import re
import frappe
from frappe import _
from frappe.utils.caching import request_cache


def is_valid_host(host: str) -> bool:
	"""Returns True if the host is a valid hostname else False."""

	return bool(re.compile(r"^[a-zA-Z0-9_-]+$").match(host))


def is_valid_email_for_domain(
	email: str, domain_name: str, raise_exception: bool = False
) -> bool:
	"""Returns True if the email domain matches with the given domain else False."""

	email_domain = email.split("@")[1]

	if not email_domain == domain_name:
		if raise_exception:
			frappe.throw(
				_("Email domain {0} does not match with domain {1}.").format(
					frappe.bold(email_domain), frappe.bold(domain_name)
				)
			)

		return False
	return True


@request_cache
def validate_domain_is_enabled_and_verified(domain_name: str) -> None:
	"""Validates if the domain is enabled and verified."""

	if frappe.flags.ingore_domain_validation:
		return

	enabled, is_verified = frappe.db.get_value(
		"Mail Domain", domain_name, ["enabled", "is_verified"]
	)

	if not enabled:
		frappe.throw(_("Domain {0} is disabled.").format(frappe.bold(domain_name)))
	if not is_verified:
		frappe.throw(_("Domain {0} is not verified.").format(frappe.bold(domain_name)))


@request_cache
def validate_mailbox_for_outgoing(mailbox: str) -> None:
	"""Validates if the mailbox is enabled and allowed for outgoing mail."""

	enabled, outgoing = frappe.db.get_value("Mailbox", mailbox, ["enabled", "outgoing"])

	if not enabled:
		frappe.throw(_("Mailbox {0} is disabled.").format(frappe.bold(mailbox)))
	elif not outgoing:
		frappe.throw(
			_("Mailbox {0} is not allowed for Outgoing Mail.").format(frappe.bold(mailbox))
		)


@request_cache
def validate_mailbox_for_incoming(mailbox: str) -> None:
	"""Validates if the mailbox is enabled and allowed for incoming mail."""

	enabled, incoming = frappe.db.get_value("Mailbox", mailbox, ["enabled", "incoming"])

	if not enabled:
		frappe.throw(_("Mailbox {0} is disabled.").format(frappe.bold(mailbox)))
	elif not incoming:
		frappe.throw(
			_("Mailbox {0} is not allowed for Incoming Mail.").format(frappe.bold(mailbox))
		)
