# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, now, now_datetime


class BounceLog(Document):
	def validate(self) -> None:
		if self.has_value_changed("bounce_count"):
			self.set_last_bounce_at()
			self.set_blocked_until()

	def set_last_bounce_at(self) -> None:
		"""Sets the last bounce at to the current time"""

		self.last_bounce_at = now()

	def set_blocked_until(self) -> None:
		"""Sets the blocked until date based on the bounce count"""

		bounce_count = self.bounce_count
		# ~1 hour, ~3 hours, 6 hours, 12 hours, 1 day, 7 days, 30 days, 100 years
		block_durations = [0.04, 0.12, 0.25, 0.5, 1, 7, 30, 36500]
		block_for_days = block_durations[min(bounce_count - 1, len(block_durations) - 1)]
		self.blocked_until = add_days(now(), block_for_days)


def create_or_update_bounce_log(email: str, bounce_increment: int = 1) -> None:
	"""Create or update the bounce log for the given email"""

	if bounce_log := frappe.db.exists("Bounce Log", {"email": email}):
		doc = frappe.get_doc("Bounce Log", bounce_log)
		doc.bounce_count += bounce_increment
	else:
		doc = frappe.new_doc("Bounce Log")
		doc.email = email
		doc.bounce_count = bounce_increment

	doc.save(ignore_permissions=True)


def is_email_blocked(email: str) -> bool:
	"""Check if a email is blocked."""

	blocked_until = frappe.get_cached_value("Bounce Log", {"email": email}, "blocked_until")
	return blocked_until and blocked_until > now_datetime()
