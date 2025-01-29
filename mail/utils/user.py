import frappe
from frappe.utils.caching import request_cache

from mail.utils.cache import get_user_mail_account, get_user_mail_aliases, get_user_mail_tenant


@request_cache
def is_system_manager(user: str) -> bool:
	"""Returns True if the user is Administrator or System Manager else False."""

	return user == "Administrator" or has_role(user, "System Manager")


def get_user_email_addresses(user: str) -> list:
	"""Returns the list of email addresses associated with the user."""

	email_addresses = []
	if account := get_user_mail_account(user):
		email_addresses.append(account)
	if aliases := get_user_mail_aliases(user):
		email_addresses.extend(aliases)

	return email_addresses


@frappe.whitelist()
def get_user_tenant() -> str | None:
	"""Returns the mail tenant of the user."""

	return get_user_mail_tenant(frappe.session.user)


@request_cache
def is_mail_tenant_owner(tenant: str, user: str) -> bool:
	"""Returns True if the user is the owner of the mail tenant else False."""

	return frappe.db.get_value("Mail Tenant", tenant, "user") == user


@request_cache
def is_mail_tenant_admin(tenant: str, user: str) -> bool:
	"""Returns True if the user is an admin of the mail tenant else False."""

	return has_role(user, "Mail Admin") and frappe.db.exists(
		"Mail Tenant Member", {"tenant": tenant, "user": user}
	)


@request_cache
def is_mail_account_owner(account: str, user: str) -> bool:
	"""Returns True if the mail account is associated with the user else False."""

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
