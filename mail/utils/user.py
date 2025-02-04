import frappe
from frappe.utils.caching import request_cache

from mail.utils.cache import get_account_for_user, get_aliases_for_user, get_tenant_for_user


@request_cache
def is_system_manager(user: str) -> bool:
	"""Returns True if the user is Administrator or System Manager else False."""

	return user == "Administrator" or has_role(user, "System Manager")


def get_user_email_addresses(user: str) -> list:
	"""Returns the list of email addresses associated with the user."""

	email_addresses = []
	if account := get_account_for_user(user):
		email_addresses.append(account)
	if aliases := get_aliases_for_user(user):
		email_addresses.extend(aliases)

	return email_addresses


def get_user_linked_domains(user: str) -> list:
	"""Returns the list of linked domains associated with the user."""

	linked_domains = set()
	if email_addresses := get_user_email_addresses(user):
		for email_address in email_addresses:
			linked_domains.add(email_address.split("@")[1])

	return list(linked_domains)


@frappe.whitelist()
def get_user_tenant() -> str | None:
	"""Returns the tenant of the user."""

	return get_tenant_for_user(frappe.session.user)


@request_cache
def is_tenant_owner(tenant: str, user: str) -> bool:
	"""Returns True if the user is the owner of the tenant else False."""

	return frappe.db.get_value("Mail Tenant", tenant, "user") == user


@request_cache
def is_tenant_admin(tenant: str, user: str) -> bool:
	"""Returns True if the user is an admin of the tenant else False."""

	return has_role(user, "Mail Admin") and frappe.db.exists(
		"Mail Tenant Member", {"tenant": tenant, "user": user, "is_admin": 1}
	)


@request_cache
def is_tenant_member(tenant: str, user: str) -> bool:
	"""Returns True if the user is a member of the tenant else False."""

	return frappe.db.exists("Mail Tenant Member", {"tenant": tenant, "user": user})


@request_cache
def is_account_owner(account: str, user: str) -> bool:
	"""Returns True if the account is associated with the user else False."""

	return frappe.db.get_value("Mail Account", account, "user") == user


@request_cache
def has_role(user: str, roles: str | list) -> bool:
	"""Returns True if the user has any of the given roles else False."""

	if isinstance(roles, str):
		roles = [roles]

	user_roles = frappe.get_roles(user)
	for role in roles:
		if role in user_roles:
			return True

	return False
