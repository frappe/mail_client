# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from typing import Optional
from frappe.model.document import Document
from mail.utils.user import is_system_manager


class MailContact(Document):
	def before_validate(self) -> None:
		self.set_user()

	def validate(self) -> None:
		self.validate_duplicate_contact()

	def set_user(self) -> None:
		"""Set user as current user if not set."""

		user = frappe.session.user
		if not self.user or not is_system_manager(user):
			self.user = user

	def validate_duplicate_contact(self) -> None:
		"""Validates if the contact is duplicate."""

		if frappe.db.exists("Mail Contact", {"email": self.email, "user": self.user}):
			frappe.throw(
				_("Mail Contact with email {0} already exists.").format(frappe.bold(self.email))
			)


def create_mail_contact(
	user: str, email: str, display_name: Optional[str] = None
) -> None:
	"""Creates the mail contact."""

	if mail_contact := frappe.db.exists("Mail Contact", {"user": user, "email": email}):
		current_display_name = frappe.get_cached_value(
			"Mail Contact", mail_contact, "display_name"
		)
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

	return is_system_manager(user) or (user == doc.user)


def get_permission_query_condition(user: Optional[str]) -> str:
	if not user:
		user = frappe.session.user

	if is_system_manager(user):
		return ""

	return f"(`tabMail Contact`.`user` = {frappe.db.escape(user)})"
