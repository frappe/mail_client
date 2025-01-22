# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MailSyncHistory(Document):
	def before_insert(self) -> None:
		self.validate_duplicate()

	def validate_duplicate(self) -> None:
		"""Validate if the Mail Sync History already exists."""

		if frappe.db.exists(
			"Mail Sync History",
			{"source": self.source, "user": self.user, "account": self.account},
		):
			frappe.throw(_("Mail Sync History already exists for this source, user and account"))


def create_mail_sync_history(
	source: str,
	user: str,
	account: str,
	last_synced_at: str | None = None,
	commit: bool = False,
) -> "MailSyncHistory":
	"""Create a Mail Sync History."""

	doc = frappe.new_doc("Mail Sync History")
	doc.source = source
	doc.user = user
	doc.account = account
	doc.last_synced_at = last_synced_at
	doc.insert(ignore_permissions=True)

	if commit:
		frappe.db.commit()

	return doc


def get_mail_sync_history(source: str, user: str, account: str) -> "MailSyncHistory":
	"""Returns the Mail Sync History for the given source, user and account."""

	if name := frappe.db.exists("Mail Sync History", {"source": source, "user": user, "account": account}):
		return frappe.get_doc("Mail Sync History", name)

	return create_mail_sync_history(source, user, account, commit=True)


def on_doctype_update() -> None:
	frappe.db.add_unique(
		"Mail Sync History",
		["source", "user", "account"],
		constraint_name="unique_source_user_account",
	)
