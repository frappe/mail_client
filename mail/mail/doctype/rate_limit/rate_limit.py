# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class RateLimit(Document):
	def validate(self) -> None:
		self.validate_key_or_ip_based()
		self.validate_methods()
		self.validate_ignored_ips()

	def on_update(self) -> None:
		self.clear_cache()

	def on_trash(self) -> None:
		self.clear_cache()

	def validate_key_or_ip_based(self) -> None:
		"""Validate key_ or IP based"""

		if not self.key_ and not self.ip_based:
			frappe.throw(_("Either key or IP flag is required."))

	def validate_methods(self) -> None:
		"""Validate methods"""

		methods = []
		if self.methods:
			for method in self.methods.split("\n"):
				if method and method not in methods:
					methods.append(method)
		self.methods = "\n".join(methods)

	def validate_ignored_ips(self) -> None:
		"""Validate ignored IPs"""

		ignored_ips = []
		if self.ignored_ips:
			for ip in self.ignored_ips.split("\n"):
				if ip and ip not in ignored_ips:
					ignored_ips.append(ip)
		self.ignored_ips = "\n".join(ignored_ips)

	def clear_cache(self) -> None:
		"""Clear cache for the rate limit"""

		frappe.cache.hdel("rate_limits", self.method_path)


def create_rate_limit(
	method_path: str,
	limit: int = 5,
	seconds: int = 86_400,
	key: str | None = None,
	ip_based: bool = True,
	methods: str = "ALL",
	ignore_in_developer_mode: bool = True,
) -> "RateLimit":
	"""Create a Rate Limit document"""

	doc = frappe.new_doc("Rate Limit")
	doc.enabled = 1
	doc.ignore_in_developer_mode = cint(ignore_in_developer_mode)
	doc.method_path = method_path
	doc.methods = methods
	doc.key_ = key
	doc.limit = limit
	doc.seconds = seconds
	doc.ip_based = cint(ip_based)
	doc.insert(ignore_permissions=True)


def on_doctype_update() -> None:
	frappe.db.add_unique(
		"Rate Limit", ["method_path", "key_", "ip_based", "seconds"], constraint_name="unique_rate_limit"
	)
