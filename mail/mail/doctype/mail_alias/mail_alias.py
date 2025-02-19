# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.agent import create_alias_on_agents, delete_alias_from_agents, patch_alias_on_agents
from mail.utils.cache import get_account_for_user, get_tenant_for_user
from mail.utils.user import has_role, is_system_manager, is_tenant_admin
from mail.utils.validation import (
	is_email_assigned,
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
	validate_domain_owned_by_tenant,
	validate_no_subaddressing,
)


class MailAlias(Document):
	def autoname(self) -> None:
		self.email = self.email.strip().lower()
		self.name = self.email

	def before_validate(self) -> None:
		self.set_tenant()

	def validate(self) -> None:
		self.validate_domain()
		self.validate_email()
		self.validate_alias_for_name()

	def on_update(self) -> None:
		self.clear_cache()

		if self.enabled:
			if self.has_value_changed("enabled") or self.has_value_changed("email"):
				create_alias_on_agents(self.alias_for_name, self.email)
			elif self.has_value_changed("alias_for_name"):
				self.remove_alias_set_as_default_outgoing_email()
				patch_alias_on_agents(
					self.alias_for_name, self.get_doc_before_save().alias_for_name, self.email
				)
		elif self.has_value_changed("enabled"):
			self.remove_alias_set_as_default_outgoing_email()
			delete_alias_from_agents(self.alias_for_name, self.email)

	def on_trash(self) -> None:
		self.clear_cache()

		if self.enabled:
			delete_alias_from_agents(self.alias_for_name, self.email)

	def set_tenant(self) -> None:
		"""Sets the tenant based on the domain."""

		if not self.tenant:
			self.tenant = frappe.db.get_value("Mail Domain", self.domain_name, "tenant")

	def validate_domain(self) -> None:
		"""Validates the domain."""

		validate_domain_owned_by_tenant(self.domain_name, self.tenant)
		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_email(self) -> None:
		"""Validates the email address."""

		validate_no_subaddressing(self.email)
		is_email_assigned(self.email, self.doctype, raise_exception=True)
		is_valid_email_for_domain(self.email, self.domain_name, raise_exception=True)

	def validate_alias_for_name(self) -> None:
		"""Validates the alias for name."""

		tenant, enabled = frappe.db.get_value(self.alias_for_type, self.alias_for_name, ["tenant", "enabled"])

		if self.tenant != tenant:
			frappe.throw(
				_("Domain {0} and {1} {2} must belong to the same tenant.").format(
					frappe.bold(self.domain_name), self.alias_for_type, frappe.bold(self.alias_for_name)
				)
			)

		if not enabled:
			frappe.throw(
				_("The {0} {1} is disabled.").format(self.alias_for_type, frappe.bold(self.alias_for_name))
			)

	def clear_cache(self) -> None:
		"""Clears the Cache."""

		frappe.cache.delete_value(f"email|{self.email}")

		if self.alias_for_type == "Mail Account":
			user = frappe.db.get_value("Mail Account", self.alias_for_name, "user")
			frappe.cache.hdel(f"user|{user}", "aliases")

		if self.has_value_changed("alias_for_type") or self.has_value_changed("alias_for_name"):
			if previous_doc := self.get_doc_before_save():
				if previous_doc.alias_for_type == "Mail Account":
					user = frappe.db.get_value("Mail Account", previous_doc.alias_for_name, "user")
					frappe.cache.hdel(f"user|{user}", "aliases")

	def remove_alias_set_as_default_outgoing_email(self) -> None:
		"""Removes the alias set as the default outgoing email."""

		if account := frappe.db.exists("Mail Account", {"default_outgoing_email": self.email}):
			account = frappe.get_doc("Mail Account", account)
			account.default_outgoing_email = None
			account.save(ignore_permissions=True)


def has_permission(doc: "Document", ptype: str, user: str | None = None) -> bool:
	if doc.doctype != "Mail Alias":
		return False

	user = user or frappe.session.user

	if is_system_manager(user):
		return True

	if is_tenant_admin(doc.tenant, user):
		return True

	if has_role(user, "Mail User"):
		return doc.alias_for_type == "Mail Account" and doc.alias_for_name == get_account_for_user(user)

	return False


def get_permission_query_condition(user: str | None = None) -> str:
	user = user or frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		if tenant := get_tenant_for_user(user):
			return f"(`tabMail Alias`.`tenant` = {frappe.db.escape(tenant)})"

	if has_role(user, "Mail User"):
		if account := get_account_for_user(user):
			return f'(`tabMail Alias`.`alias_for_type` = "Mail Account" AND `tabMail Alias`.`alias_for_name` = {frappe.db.escape(account)})'

	return "1=0"
