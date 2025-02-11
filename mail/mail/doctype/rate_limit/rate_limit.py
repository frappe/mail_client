# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint


class RateLimit(Document):
	def on_update(self) -> None:
		self.clear_cache()

	def on_trash(self) -> None:
		self.clear_cache()

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
	doc.key = key
	doc.limit = limit
	doc.seconds = seconds
	doc.ip_based = cint(ip_based)
	doc.insert(ignore_permissions=True)


def on_doctype_update() -> None:
	frappe.db.add_unique(
		"Rate Limit", ["method_path", "key_", "ip_based", "seconds"], constraint_name="unique_rate_limit"
	)
