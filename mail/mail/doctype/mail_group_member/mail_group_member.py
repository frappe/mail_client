# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.agent import create_member_on_agents, delete_member_from_agents
from mail.utils.cache import get_groups_owned_by_tenant, get_tenant_for_user
from mail.utils.user import has_role, is_system_manager


class MailGroupMember(Document):
	@property
	def member_is_group(self) -> bool:
		"""Return True if the member is a mail group"""

		return self.member_type == "Mail Group"

	def validate(self) -> None:
		self.validate_mail_group()
		self.validate_member_tenant()
		self.validate_member_name()

	def validate_mail_group(self) -> None:
		"""Validate if the mail group is enabled."""

		if not frappe.db.get_value("Mail Group", self.mail_group, "enabled"):
			frappe.throw(_("The Mail Group {0} is disabled.").format(frappe.bold(self.mail_group)))

	def validate_member_tenant(self) -> None:
		"""Validate if the mail group and the member belong to the same tenant."""

		group_tenant = frappe.db.get_value("Mail Group", self.mail_group, "tenant")
		member_tenant = frappe.db.get_value(self.member_type, self.member_name, "tenant")

		if group_tenant != member_tenant:
			frappe.throw(
				_("The Mail Group {0} and the member {1} {2} must belong to the same tenant.").format(
					frappe.bold(self.mail_group), self.member_type, frappe.bold(self.member_name)
				)
			)

	def validate_member_name(self) -> None:
		"""Validate if the member name is not the same as the mail group"""

		if self.mail_group == self.member_name:
			if self.member_type == "Mail Group":
				frappe.throw(_("Mail Group cannot be a member of itself"))
			else:
				frappe.throw(_("Member cannot be the same as the Mail Group"))

		if not frappe.db.get_value(self.member_type, self.member_name, "enabled"):
			frappe.throw(
				_("The {0} {1} is disabled.").format(self.member_type, frappe.bold(self.member_name))
			)

	def after_insert(self) -> None:
		create_member_on_agents(self.mail_group, self.member_name, self.member_is_group)

	def on_trash(self) -> None:
		delete_member_from_agents(self.mail_group, self.member_name, self.member_is_group)


def has_permission(doc: "Document", ptype: str, user: str | None = None) -> bool:
	if doc.doctype != "Mail Group Member":
		return False

	user = user or frappe.session.user

	if is_system_manager(user):
		return True

	if has_role(user, "Mail Admin"):
		if tenant := get_tenant_for_user(user):
			return doc.mail_group in get_groups_owned_by_tenant(tenant)

	return False


def get_permission_query_condition(user: str | None = None) -> str:
	user = user or frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		if tenant := get_tenant_for_user(user):
			if groups := get_groups_owned_by_tenant(tenant):
				return f'(`tabMail Group Member`.`mail_group` IN ({", ".join([frappe.db.escape(group) for group in groups])}))'

	return "1=0"


def on_doctype_update() -> None:
	frappe.db.add_unique(
		"Mail Group Member",
		["mail_group", "member_name"],
		constraint_name="unique_mail_group_member",
	)
