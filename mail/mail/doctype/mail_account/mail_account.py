# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from typing import Literal

import bcrypt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import random_string

from mail.agent import create_account_on_agents, delete_account_from_agents, patch_account_on_agents
from mail.utils import get_dmarc_address
from mail.utils.cache import get_aliases_for_user, get_tenant_for_user
from mail.utils.user import has_role, is_system_manager
from mail.utils.validation import (
	is_email_assigned,
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
)


class MailAccount(Document):
	def autoname(self) -> None:
		self.email = self.email.strip().lower()
		self.name = self.email

	def before_validate(self) -> None:
		self.set_tenant()

	def validate(self) -> None:
		self.validate_enabled()
		self.validate_domain()
		self.validate_user()
		self.validate_user_tenant()
		self.validate_email()
		self.validate_password()
		self.validate_default_outgoing_email()
		self.validate_display_name()

	def on_update(self) -> None:
		self.clear_cache()

		if self.enabled:
			if self.has_value_changed("enabled") or self.has_value_changed("email"):
				create_account_on_agents(self.email, self.display_name, self.secret)
			elif self.has_value_changed("display_name") or self.has_value_changed("secret"):
				patch_account_on_agents(
					self.email, self.display_name, self.secret, self.get_doc_before_save().secret
				)
		elif self.has_value_changed("enabled"):
			delete_account_from_agents(self.email)

	def on_trash(self) -> None:
		self.clear_cache()

		if self.enabled:
			delete_account_from_agents(self.email)

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

		if frappe.db.exists("Mail Group Member", {"member_type": self.doctype, "member_name": self.name}):
			frappe.throw(_("This account is linked to a mail group. Please remove it first."))

	def validate_domain(self) -> None:
		"""Validates the domain."""

		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_user(self) -> None:
		"""Validates the user."""

		if not has_role(self.user, "Mail User"):
			frappe.throw(_("User {0} does not have Mail User role.").format(frappe.bold(self.user)))

	def validate_user_tenant(self) -> None:
		"""Validates the user tenant."""

		if self.is_new() or self.enabled:
			if self.tenant != get_tenant_for_user(self.user):
				frappe.throw(
					_("Domain {0} and User {1} do not belong to the same tenant.").format(
						frappe.bold(self.domain_name), frappe.bold(self.user)
					)
				)

	def validate_email(self) -> None:
		"""Validates the email address."""

		if not self.email:
			frappe.throw(_("Email is mandatory."))

		is_email_assigned(self.email, self.doctype, raise_exception=True)
		is_valid_email_for_domain(self.email, self.domain_name, raise_exception=True)

	def validate_password(self) -> None:
		"""Generates secret if password is changed"""

		if not self.password:
			self.password = random_string(length=20)

		if not self.is_new():
			if previous_doc := self.get_doc_before_save():
				if previous_doc.get_password("password") == self.get_password("password"):
					return

		self.generate_secret()

	def validate_default_outgoing_email(self) -> None:
		"""Validates the default outgoing email."""

		if not self.default_outgoing_email:
			self.default_outgoing_email = self.email
		else:
			if self.default_outgoing_email not in [self.email] + get_aliases_for_user(self.user):
				frappe.throw(_("Default Email must be one of the email addresses assigned to the user."))

	def validate_display_name(self) -> None:
		"""Validates the display name."""

		if self.is_new() and not self.display_name:
			self.display_name = frappe.db.get_value("User", self.user, "full_name")

	def clear_cache(self) -> None:
		"""Clears the Cache."""

		frappe.cache.delete_value(f"user|{self.user}")
		frappe.cache.delete_value(f"email|{self.email}")

	def generate_secret(self) -> None:
		"""Generates secret from password"""

		password = self.get_password("password").encode("utf-8")
		salt = bcrypt.gensalt()
		self.secret = bcrypt.hashpw(password, salt).decode()


def create_mail_account(
	email: str,
	first_name: str,
	last_name: str | None = None,
	password: str | None = None,
	role: Literal["Mail User", "Mail Admin"] = "Mail User",
) -> "MailAccount":
	"""Creates a Mail Account"""

	if role not in ["Mail User", "Mail Admin"]:
		frappe.throw(_("Invalid role. Please select a valid role."))

	roles = ["Mail User"]
	if role == "Mail Admin":
		roles.append("Mail Admin")

	if not frappe.db.exists("Mail Account", email):
		if not frappe.db.exists("User", {"email": email}):
			account_user = frappe.new_doc("User")
			account_user.first_name = first_name
			account_user.last_name = last_name
			account_user.username = email
			account_user.email = email
			account_user.owner = email
			account_user.send_welcome_email = 0
			account_user.append_roles(*roles)
			if password:
				account_user.new_password = password
			account_user.insert(ignore_permissions=True)
		else:
			frappe.throw(_("User with email {0} already exists.").format(frappe.bold(email)))

		account = frappe.new_doc("Mail Account")
		account.domain_name = email.split("@")[1]
		account.user = email
		account.insert(ignore_permissions=True)

		return account
	else:
		frappe.throw(_("Mail Account {0} already exists.").format(frappe.bold(email)))


def create_dmarc_account() -> None:
	"""Creates a DMARC account"""

	frappe.flags.ignore_domain_validation = True
	create_mail_account(email=get_dmarc_address(), first_name="DMARC")


def has_permission(doc: "Document", ptype: str, user: str) -> bool:
	if doc.doctype != "Mail Account":
		return False

	if is_system_manager(user):
		return True

	if has_role(user, "Mail Admin"):
		return doc.tenant == get_tenant_for_user(user)

	return user == doc.user


def get_permission_query_condition(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		return f"(`tabMail Account`.`tenant` = {frappe.db.escape(get_tenant_for_user(user))})"

	return f"(`tabMail Account`.`user` = {frappe.db.escape(user)})"
