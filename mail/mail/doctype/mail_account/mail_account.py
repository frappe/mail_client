# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import crypt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import random_string

from mail.mail.doctype.mail_agent_job.mail_agent_job import (
	create_account_on_agents,
	delete_account_from_agents,
	patch_account_on_agents,
)
from mail.utils.user import has_role
from mail.utils.validation import (
	is_email_assigned,
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
)


class MailAccount(Document):
	def autoname(self) -> None:
		self.email = self.email.strip().lower()
		self.name = self.email

	def validate(self) -> None:
		self.validate_enabled()
		self.validate_domain()
		self.validate_user()
		self.validate_email()
		self.validate_password()
		self.validate_display_name()
		self.validate_default_account()

	def on_update(self) -> None:
		frappe.cache.delete_value(f"user|{self.user}")

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
		frappe.cache.delete_value(f"user|{self.user}")

		if self.enabled:
			delete_account_from_agents(self.email)

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

	def validate_email(self) -> None:
		"""Validates the email address."""

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

	def validate_display_name(self) -> None:
		"""Validates the display name."""

		if self.is_new() and not self.display_name:
			self.display_name = frappe.db.get_value("User", self.user, "full_name")

	def validate_default_account(self) -> None:
		"""Validates the default account."""

		if not self.enabled:
			self.is_default = 0
			return

		filters = {"user": self.user, "enabled": 1, "is_default": 1, "name": ["!=", self.name]}
		has_default_account = frappe.db.exists("Mail Account", filters)

		if self.is_default:
			if has_default_account:
				frappe.db.set_value("Mail Account", filters, "is_default", 0)
		elif not has_default_account:
			self.is_default = 1

	def generate_secret(self) -> None:
		"""Generates secret from password"""

		password = self.get_password("password")
		salt = crypt.mksalt(crypt.METHOD_SHA512)
		self.secret = crypt.crypt(password, salt)
