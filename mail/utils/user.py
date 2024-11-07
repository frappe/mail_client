from typing import Literal

import frappe
from frappe.utils.caching import request_cache

from mail.utils.cache import get_user_incoming_mailboxes, get_user_outgoing_mailboxes


@request_cache
def is_system_manager(user: str) -> bool:
	"""Returns True if the user is Administrator or System Manager else False."""

	return user == "Administrator" or has_role(user, "System Manager")


def get_user_mailboxes(user: str, type: Literal["Incoming", "Outgoing"] | None = None) -> list:
	"""Returns the list of mailboxes associated with the user."""

	if type and type in ["Incoming", "Outgoing"]:
		if type == "Incoming":
			return get_user_incoming_mailboxes(user)
		else:
			return get_user_outgoing_mailboxes(user)

	unique_mailboxes = set(get_user_incoming_mailboxes(user)) | set(get_user_outgoing_mailboxes(user))

	return list(unique_mailboxes)


@request_cache
def is_mailbox_owner(mailbox: str, user: str) -> bool:
	"""Returns True if the mailbox is associated with the user else False."""

	return frappe.db.get_value("Mailbox", mailbox, "user") == user


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
