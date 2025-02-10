# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.agent import create_group_on_agents, delete_group_from_agents, patch_group_on_agents
from mail.utils.cache import get_tenant_for_user
from mail.utils.user import has_role, is_system_manager, is_tenant_admin
from mail.utils.validation import (
	is_email_assigned,
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
	validate_domain_owned_by_tenant,
)


class MailGroup(Document):
	def autoname(self) -> None:
		self.email = self.email.strip().lower()
		self.name = self.email

	def before_validate(self) -> None:
		self.set_tenant()

	def validate(self) -> None:
		self.validate_enabled()
		self.validate_domain()
		self.validate_email()
		self.validate_tenant_max_groups()

	def on_update(self) -> None:
		self.clear_cache()

		if self.enabled:
			if self.has_value_changed("enabled") or self.has_value_changed("email"):
				create_group_on_agents(self.email, self.display_name)
			elif self.has_value_changed("display_name"):
				patch_group_on_agents(self.email, self.display_name)
		elif self.has_value_changed("enabled"):
			delete_group_from_agents(self.email)

	def on_trash(self) -> None:
		self.clear_cache()

		if self.enabled:
			delete_group_from_agents(self.email)

	def set_tenant(self) -> None:
		"""Sets the tenant based on the domain."""

		if not self.tenant:
			self.tenant = frappe.db.get_value("Mail Domain", self.domain_name, "tenant")

	def validate_enabled(self) -> None:
		"""Validates the enabled field."""

		if self.enabled:
			return

		if alias := frappe.db.exists(
			"Mail Alias", {"enabled": 1, "alias_for_type": self.doctype, "alias_for_name": self.name}
		):
			frappe.throw(_("Mail Alias {0} is enabled. Please disable it first.").format(frappe.bold(alias)))

		if frappe.db.exists("Mail Group Member", {"mail_group": self.name}):
			frappe.throw(_("Group has members. Please remove them first."))

	def validate_domain(self) -> None:
		"""Validates the domain."""

		validate_domain_owned_by_tenant(self.domain_name, self.tenant)
		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_email(self) -> None:
		"""Validates the email address."""

		is_email_assigned(self.email, self.doctype, raise_exception=True)
		is_valid_email_for_domain(self.email, self.domain_name, raise_exception=True)

	def validate_tenant_max_groups(self) -> None:
		"""Validates the Tenant Max Groups."""

		total_groups = frappe.db.count("Mail Group", filters={"tenant": self.tenant, "enabled": 1})
		max_groups = frappe.db.get_value("Mail Tenant", self.tenant, "max_groups")
		if total_groups >= max_groups:
			frappe.throw(
				_("You have reached the maximum limit of {0} groups for the tenant.").format(
					frappe.bold(max_groups)
				)
			)

	def clear_cache(self) -> None:
		"""Clears the Cache."""

		frappe.cache.hdel(f"tenant|{self.tenant}", "groups")

		if self.has_value_changed("tenant"):
			if previous_doc := self.get_doc_before_save():
				if previous_doc.tenant:
					frappe.cache.hdel(f"tenant|{previous_doc.tenant}", "groups")


def has_permission(doc: "Document", ptype: str, user: str | None = None) -> bool:
	if doc.doctype != "Mail Group":
		return False

	user = user or frappe.session.user

	if is_system_manager(user):
		return True

	if is_tenant_admin(doc.tenant, user):
		return True

	return False


def get_permission_query_condition(user: str | None = None) -> str:
	user = user or frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		if tenant := get_tenant_for_user(user):
			return f"(`tabMail Group`.`tenant` = {frappe.db.escape(tenant)})"

	return "1=0"
