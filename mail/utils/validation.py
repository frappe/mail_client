import ipaddress
import re
import socket

import frappe
from frappe import _
from frappe.utils.caching import request_cache
from validate_email_address import validate_email

from mail.utils.cache import get_user_owned_domains
from mail.utils.user import has_role


def is_valid_host(host: str) -> bool:
	"""Returns True if the host is a valid hostname else False."""

	return bool(re.compile(r"^[a-zA-Z0-9_-]+$").match(host))


def is_valid_ip_address(ip_address: str, category: str | None = None) -> bool:
	"""Returns True if the IP address is valid else False."""

	try:
		ip_obj = ipaddress.ip_address(ip_address)

		if category:
			if category == "private":
				return ip_obj.is_private
			elif category == "public":
				return not ip_obj.is_private

		return True
	except ValueError:
		return False


def is_port_open(fqdn: str, port: int, timeout: int = 10) -> bool:
	"""Returns True if the port is open else False."""

	try:
		with socket.create_connection((fqdn, port), timeout=timeout):
			return True
	except (TimeoutError, OSError):
		return False


def is_email_assigned(email: str, ignore_doctype: str | None = None, raise_exception: bool = False) -> bool:
	"""Returns True if the email is already assigned to Mail Account, Mail Group, or Mail Alias else False."""

	doctypes = ["Mail Account", "Mail Group", "Mail Alias"]
	if ignore_doctype:
		doctypes.remove(ignore_doctype)

	for doctype in doctypes:
		if frappe.db.exists(doctype, {"email": email}):
			if raise_exception:
				frappe.throw(
					_("The email address {0} is already in use and assigned to {1}.").format(
						frappe.bold(email), frappe.bold(doctype)
					)
				)

			return True
	return False


def is_valid_email_for_domain(email: str, domain_name: str, raise_exception: bool = False) -> bool:
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


def validate_email_address(
	email: str, check_mx: bool = True, verify: bool = True, smtp_timeout: int = 10
) -> bool:
	"""Validates the email address by checking MX records and RCPT TO."""

	return bool(validate_email(email=email, check_mx=check_mx, verify=verify, smtp_timeout=smtp_timeout))


@request_cache
def validate_domain_is_enabled_and_verified(domain_name: str) -> None:
	"""Validates if the domain is enabled and verified."""

	if frappe.flags.ingore_domain_validation:
		return

	enabled, is_verified = frappe.db.get_value("Mail Domain", domain_name, ["enabled", "is_verified"])

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
		frappe.throw(_("Mailbox {0} is not allowed for Outgoing Mail.").format(frappe.bold(mailbox)))


@request_cache
def validate_mailbox_for_incoming(mailbox: str) -> None:
	"""Validates if the mailbox is enabled and allowed for incoming mail."""

	enabled, incoming = frappe.db.get_value("Mailbox", mailbox, ["enabled", "incoming"])

	if not enabled:
		frappe.throw(_("Mailbox {0} is disabled.").format(frappe.bold(mailbox)))
	elif not incoming:
		frappe.throw(_("Mailbox {0} is not allowed for Incoming Mail.").format(frappe.bold(mailbox)))


def validate_user_has_domain_owner_role(user: str) -> None:
	"""Validate if the user has Domain Owner role or System Manager role."""

	if not has_role(user, "Domain Owner"):
		frappe.throw(_("You are not authorized to perform this action."), frappe.PermissionError)


def validate_user_is_domain_owner(user: str, domain_name: str) -> None:
	"""Validate if the user is the owner of the given domain."""

	if domain_name not in get_user_owned_domains(user):
		frappe.throw(
			_("The domain {0} does not belong to user {1}.").format(
				frappe.bold(domain_name), frappe.bold(user)
			),
			frappe.PermissionError,
		)


def is_domain_exists(domain_name: str, exclude_disabled: bool = True, raise_exception: bool = False) -> bool:
	"""Validate if the domain exists in the Mail Domain."""

	filters = {"domain_name": domain_name}
	if exclude_disabled:
		filters["enabled"] = 1

	if frappe.db.exists("Mail Domain", filters):
		return True

	if raise_exception:
		if exclude_disabled:
			frappe.throw(
				_("Domain {0} does not exist or may be disabled in the Mail Domain.").format(
					frappe.bold(domain_name)
				),
				frappe.DoesNotExistError,
			)

		frappe.throw(
			_("Domain {0} not found in Mail Domain.").format(frappe.bold(domain_name)),
			frappe.DoesNotExistError,
		)

	return False
