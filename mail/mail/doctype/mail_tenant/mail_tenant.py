# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document

from mail.utils.cache import get_user_mail_tenant
from mail.utils.user import has_role, is_mail_tenant_admin, is_system_manager


class MailTenant(Document):
	def validate(self) -> None:
		self.validate_user()

	def validate_user(self) -> None:
		"""Validates the user."""

		if not has_role(self.user, "Mail Admin"):
			frappe.throw(_("User {0} does not have Mail Admin role.").format(frappe.bold(self.user)))

	def after_insert(self) -> None:
		"""Add the user as a member of the tenant."""

		self.add_member(self.user)

	def add_member(self, user: str) -> str:
		"""Add a member to the tenant."""

		member = frappe.new_doc("Mail Tenant Member")
		member.tenant = self.name
		member.user = user
		member.insert(ignore_permissions=True)

		return member.name

	def remove_member(self, user: str) -> None:
		"""Remove a member from the tenant."""

		frappe.db.delete("Mail Tenant Member", {"tenant": self.name, "user": user})

	def has_member(self, user: str) -> bool:
		"""Check if the user is a member of the tenant."""

		return frappe.db.exists("Mail Tenant Member", {"tenant": self.name, "user": user})


def has_permission(doc: "Document", ptype: str, user: str) -> bool:
	if doc.doctype != "Mail Tenant":
		return False

	if is_system_manager(user):
		return True

	if is_mail_tenant_admin(doc.name, user):
		if ptype in ("read", "write"):
			return True

	return False


def get_permission_query_condition(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		if tenant := get_user_mail_tenant(user):
			return f'(`tabMail Tenant`.`name` = "{tenant}")'

	return "1=0"
