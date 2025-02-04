import ipaddress
import re
import socket

import frappe
from frappe import _
from frappe.utils.caching import request_cache
from validate_email_address import validate_email

from mail.utils.cache import get_tenant_for_user
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
					_("The email address {0} is already assigned as a {1}.").format(
						frappe.bold(email), frappe.bold(doctype)
					)
				)

			return True
	return False


def is_valid_email_for_domain(email: str, domain_name: str, raise_exception: bool = False) -> bool:
	"""Returns True if the email domain matches with the given domain else False."""

	email_domain = email.split("@")[1]

	if email_domain != domain_name:
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

	if frappe.flags.ignore_domain_validation:
		return

	enabled, is_verified = frappe.db.get_value("Mail Domain", domain_name, ["enabled", "is_verified"])

	if not enabled:
		frappe.throw(_("Domain {0} is disabled.").format(frappe.bold(domain_name)))
	if not is_verified:
		frappe.throw(_("Domain {0} is not verified.").format(frappe.bold(domain_name)))


@request_cache
def validate_domain_owned_by_tenant(domain_name: str, tenant: str) -> None:
	"""Validates if the domain is owned by the tenant."""

	if tenant != frappe.db.get_value("Mail Domain", domain_name, "tenant"):
		frappe.throw(_("Domain {0} is not owned by the tenant.").format(frappe.bold(domain_name)))


@request_cache
def validate_domain_owned_by_user_tenant(domain_name: str, user: str) -> None:
	"""Validates if the domain is owned by the user tenant."""

	validate_domain_owned_by_tenant(domain_name, get_tenant_for_user(user))


def validate_domain_and_user_tenant(domain_name: str, user: str) -> None:
	"""Validates if the domain and user belong to the same tenant."""

	domain_tenant = frappe.db.get_value("Mail Domain", domain_name, "tenant")
	user_tenant = get_tenant_for_user(user)

	if domain_tenant != user_tenant:
		frappe.throw(
			_("Domain {0} and User {1} do not belong to the same tenant.").format(
				frappe.bold(domain_name), frappe.bold(user)
			)
		)


def validate_user_has_mail_admin_role(user: str) -> None:
	"""Validate if the user has Mail Admin role or System Manager role."""

	if not has_role(user, "Mail Admin"):
		frappe.throw(_("You are not authorized to perform this action."), frappe.PermissionError)


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
