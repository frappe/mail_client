# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.utils.cache import get_tenant_for_user
from mail.utils.user import has_role, is_mail_tenant_admin, is_mail_tenant_owner, is_system_manager


class MailTenantMember(Document):
	def validate(self) -> None:
		self.validate_user()

	def on_update(self) -> None:
		self.clear_cache()

	def on_trash(self) -> None:
		if is_mail_tenant_owner(self.tenant, self.user):
			frappe.throw(_("Cannot remove the owner of the Mail Tenant."))

		self.clear_cache()

	def validate_user(self) -> None:
		"""Validates if the user is a valid user and has the required roles."""

		if tenant := frappe.db.get_value("Mail Tenant Member", {"user": self.user}, "tenant"):
			if tenant == self.tenant:
				frappe.throw(_("User {0} is already a member.").format(frappe.bold(self.user)))
			else:
				frappe.throw(
					_("User {0} is already a member of another Mail Tenant.").format(
						frappe.bold(self.user), frappe.bold(tenant)
					)
				)

		if not has_role(self.user, ["Mail Admin", "Mail User"]):
			frappe.throw(
				_("User {0} does not have Mail Admin or Mail User role.").format(frappe.bold(self.user))
			)

	def clear_cache(self) -> None:
		"""Clears the Cache."""

		frappe.cache.delete_value(f"user|{self.user}")


def has_permission(doc: "Document", ptype: str, user: str) -> bool:
	if doc.doctype != "Mail Tenant Member":
		return False

	if is_system_manager(user):
		return True

	if is_mail_tenant_admin(doc.tenant, user):
		return True

	return False


def get_permission_query_condition(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		if tenant := get_tenant_for_user(user):
			return f'(`tabMail Tenant Member`.`tenant` = "{tenant}")'

	return "1=0"
