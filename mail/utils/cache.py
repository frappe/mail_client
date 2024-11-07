from typing import Any

import frappe
from frappe import _


def _get_or_set(name: str, getter: callable, expires_in_sec: int | None = 60 * 60) -> Any | None:
	"""Get or set a value in the cache."""

	value = frappe.cache.get_value(name)

	if not value:
		value = getter()
		frappe.cache.set_value(name, value, expires_in_sec=expires_in_sec)

	if isinstance(value, bytes):
		value = value.decode()

	return value


def _hget_or_hset(name: str, key: str, getter: callable) -> Any | None:
	"""Get or set a value in the cache hash."""

	value = frappe.cache.hget(name, key)

	if not value:
		value = getter()
		frappe.cache.hset(name, key, value)

	return value


def delete_cache(name: str, key: str | None = None) -> None:
	"""Delete a value from the cache."""

	if not key:
		frappe.cache.delete_value(name)
	else:
		frappe.cache.hdel(name, key)


def get_postmaster_for_domain(domain_name: str) -> str:
	"""Returns the postmaster for the domain."""

	def getter() -> str:
		postmaster = frappe.db.get_value(
			"Mailbox",
			{
				"enabled": 1,
				"outgoing": 1,
				"postmaster": 1,
				"domain_name": domain_name,
				"user": "Administrator",
			},
			"name",
		)

		if not postmaster:
			frappe.throw(_("Postmaster not found for {0}").format(domain_name))

		return postmaster

	return _get_or_set(f"postmaster|{domain_name}", getter)


def get_user_incoming_mailboxes(user: str) -> list:
	"""Returns the incoming mailboxes of the user."""

	def getter() -> list:
		MAILBOX = frappe.qb.DocType("Mailbox")
		return (
			frappe.qb.from_(MAILBOX)
			.select("name")
			.where((MAILBOX.user == user) & (MAILBOX.enabled == 1) & (MAILBOX.incoming == 1))
		).run(pluck="name")

	return _hget_or_hset(f"user|{user}", "incoming_mailboxes", getter)


def get_user_outgoing_mailboxes(user: str) -> list:
	"""Returns the outgoing mailboxes of the user."""

	def getter() -> list:
		MAILBOX = frappe.qb.DocType("Mailbox")
		return (
			frappe.qb.from_(MAILBOX)
			.select("name")
			.where((MAILBOX.user == user) & (MAILBOX.enabled == 1) & (MAILBOX.outgoing == 1))
		).run(pluck="name")

	return _hget_or_hset(f"user|{user}", "outgoing_mailboxes", getter)


def get_user_default_mailbox(user: str) -> str | None:
	"""Returns the default mailbox of the user."""

	def getter() -> str | None:
		return frappe.db.get_value("Mailbox", {"user": user, "is_default": 1}, "name")

	return _hget_or_hset(f"user|{user}", "default_mailbox", getter)
