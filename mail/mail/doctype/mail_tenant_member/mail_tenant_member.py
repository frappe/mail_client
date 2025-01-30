# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.utils.cache import get_tenant_for_user
from mail.utils.user import has_role, is_system_manager, is_tenant_admin, is_tenant_owner


class MailTenantMember(Document):
	def validate(self) -> None:
		if self.is_new():
			self.validate_user()

		self.validate_user_roles()
		self.validate_is_admin()

	def on_update(self) -> None:
		self.clear_cache()

	def on_trash(self) -> None:
		if is_tenant_owner(self.tenant, self.user):
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

	def validate_user_roles(self) -> None:
		"""Validates if the user has the required roles to be a member of the Mail Tenant."""

		# Tenant Owner must have Mail Admin role.
		# Tenant Member must have Mail User role and can have Mail Admin role.
		required_role = "Mail Admin" if is_tenant_owner(self.tenant, self.user) else "Mail User"
		if not has_role(self.user, required_role):
			frappe.throw(
				_("User {0} does not have {1} role.").format(
					frappe.bold(self.user), frappe.bold(required_role)
				)
			)

	def validate_is_admin(self) -> None:
		"""Validates if the user is an admin of the Mail Tenant."""

		if is_tenant_owner(self.tenant, self.user):
			self.is_admin = 1
			return

		has_admin_role = has_role(self.user, "Mail Admin")

		if self.is_admin and not has_admin_role:
			user = frappe.get_doc("User", self.user)
			user.append("roles", {"role": "Mail Admin"})
			user.save(ignore_permissions=True)
			frappe.msgprint(
				_("Mail Admin role has been assigned to the user {0}.").format(frappe.bold(self.user))
			)

		elif not self.is_admin and has_admin_role:
			user = frappe.get_doc("User", self.user)
			for role in user.get("roles")[:]:
				if role.role == "Mail Admin":
					user.get("roles").remove(role)
					user.save(ignore_permissions=True)
					frappe.msgprint(
						_("Mail Admin role has been removed from the user {0}.").format(
							frappe.bold(self.user)
						)
					)
					break

	def clear_cache(self) -> None:
		"""Clears the Cache."""

		frappe.cache.delete_value(f"user|{self.user}")


def has_permission(doc: "Document", ptype: str, user: str) -> bool:
	if doc.doctype != "Mail Tenant Member":
		return False

	if is_system_manager(user):
		return True

	if is_tenant_admin(doc.tenant, user):
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
