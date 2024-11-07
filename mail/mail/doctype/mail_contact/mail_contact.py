# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.utils.user import is_system_manager


class MailContact(Document):
	def before_validate(self) -> None:
		self.set_user()

	def validate(self) -> None:
		if self.is_new():
			self.validate_duplicate_contact()

	def set_user(self) -> None:
		"""Set user as current user if not set."""

		if not self.user:
			user = frappe.session.user
			self.user = user

	def validate_duplicate_contact(self) -> None:
		"""Validates if the contact is duplicate."""

		if frappe.db.exists("Mail Contact", {"user": self.user, "email": self.email}):
			frappe.throw(_("Mail Contact with email {0} already exists.").format(frappe.bold(self.email)))


def create_mail_contact(user: str, email: str, display_name: str | None = None) -> None:
	"""Creates the mail contact."""

	if mail_contact := frappe.db.exists("Mail Contact", {"user": user, "email": email}):
		current_display_name = frappe.get_cached_value("Mail Contact", mail_contact, "display_name")
		if display_name != current_display_name:
			frappe.db.set_value("Mail Contact", mail_contact, "display_name", display_name)
	else:
		doc = frappe.new_doc("Mail Contact")
		doc.user = user
		doc.email = email
		doc.display_name = display_name
		doc.insert()


def has_permission(doc: "Document", ptype: str, user: str) -> bool:
	if doc.doctype != "Mail Contact":
		return False

	return (user == doc.user) or is_system_manager(user)


def get_permission_query_condition(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if is_system_manager(user):
		return ""

	return f"(`tabMail Contact`.`user` = {frappe.db.escape(user)})"


def on_doctype_update() -> None:
	frappe.db.add_unique("Mail Contact", ["user", "email"], constraint_name="unique_user_email")
