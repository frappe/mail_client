# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import ipaddress
from typing import Literal

import frappe
from frappe import _
from frappe.model.document import Document

from mail.agent import block_ip_on_agents, unblock_ip_on_agents
from mail.utils.cache import get_blacklist_for_ip_group
from mail.utils.dns import get_host_by_ip


class IPBlacklist(Document):
	def validate(self) -> None:
		if self.is_new():
			self.set_ip_version()
			self.set_ip_address_expanded()
			self.set_ip_group()
			self.set_source_ip_address()
			self.set_source_host()

		self.set_host()

	def on_update(self) -> None:
		self.clear_cache()

		if self.is_blacklisted:
			if self.has_value_changed("is_blacklisted"):
				block_ip_on_agents(self.ip_address)
		elif self.has_value_changed("is_blacklisted"):
			unblock_ip_on_agents(self.ip_address)

	def on_trash(self) -> None:
		self.clear_cache()

		if self.is_blacklisted:
			unblock_ip_on_agents(self.ip_address)

	def set_ip_version(self) -> None:
		"""Sets the IP version of the IP address"""

		self.ip_version = get_ip_version(self.ip_address)

	def set_ip_address_expanded(self) -> None:
		"""Sets the expanded version of the IP address"""

		self.ip_address_expanded = get_ip_address_expanded(self.ip_version, self.ip_address)

	def set_ip_group(self) -> None:
		"""Sets the IP group"""

		self.ip_group = get_ip_group(self.ip_version, self.ip_address_expanded)

	def set_source_ip_address(self) -> None:
		"""Sets the source IP address"""

		self.source_ip_address = frappe.local.request_ip

	def set_source_host(self) -> None:
		"""Sets the source host"""

		self.source_host = get_host_by_ip(self.source_ip_address)

	def set_host(self) -> None:
		"""Sets the host for the IP address"""

		self.host = get_host_by_ip(self.ip_address_expanded)

	def clear_cache(self) -> None:
		"""Clears the Cache."""

		frappe.cache.delete_value(f"blacklist|{self.ip_group}")


def get_ip_version(ip_address: str) -> Literal["IPv4", "IPv6"]:
	"""Returns the IP version of the IP address"""

	return "IPv6" if ":" in ip_address else "IPv4"


def get_ip_address_expanded(ip_version: Literal["IPv4", "IPv6"], ip_address: str) -> str:
	"""Returns the expanded version of the IP address"""

	return (
		str(ipaddress.IPv6Address(ip_address).exploded)
		if ip_version == "IPv6"
		else str(ipaddress.IPv4Address(ip_address))
	)


def get_ip_group(ip_version: Literal["IPv4", "IPv6"], ip_address: str) -> str:
	"""Returns the IP group"""

	if ip_version == "IPv6":
		return ":".join(ip_address.split(":")[:3])
	else:
		return ".".join(ip_address.split(".")[:2])


def create_ip_blacklist(
	ip_address: str, blacklist_reason: str | None = None, is_blacklisted: bool = True
) -> IPBlacklist | None:
	"""Create an IP Blacklist document"""

	try:
		doc = frappe.new_doc("IP Blacklist")
		doc.ip_address = ip_address
		doc.blacklist_reason = blacklist_reason
		doc.is_blacklisted = is_blacklisted
		doc.insert(
			ignore_permissions=True,
			ignore_if_duplicate=True,
		)
		return doc
	except Exception:
		frappe.log_error(title=_("Error creating IP Blacklist"), message=frappe.get_traceback())


def get_blacklist_for_ip_address(
	ip_address: str, create_if_not_exists: bool = False, commit: bool = False
) -> dict | None:
	"""Returns the blacklist for the IP address"""

	ip_version = get_ip_version(ip_address)
	ip_address_expanded = get_ip_address_expanded(ip_version, ip_address)
	ip_group = get_ip_group(ip_version, ip_address_expanded)

	if blacklist_group := get_blacklist_for_ip_group(ip_group):
		for blacklist in blacklist_group:
			if blacklist["ip_address"] == ip_address:
				return blacklist

	if not create_if_not_exists:
		return

	if blacklist := create_ip_blacklist(ip_address, is_blacklisted=False):
		if commit:
			frappe.db.commit()

		return {
			"name": blacklist.name,
			"is_blacklisted": blacklist.is_blacklisted,
			"ip_address": blacklist.ip_address,
			"ip_address_expanded": blacklist.ip_address_expanded,
			"blacklist_reason": blacklist.blacklist_reason,
		}
