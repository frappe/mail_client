# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RateLimit(Document):
	def on_update(self) -> None:
		self.clear_cache()

	def on_trash(self) -> None:
		self.clear_cache()

	def clear_cache(self) -> None:
		"""Clear cache for the rate limit"""

		frappe.cache.hdel("rate_limits", self.method_path)
