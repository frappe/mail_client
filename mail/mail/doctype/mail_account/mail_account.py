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
		self.validate_domain()
		self.validate_user()
		self.validate_email()
		self.validate_password()
		self.validate_display_name()

	def on_update(self) -> None:
		frappe.cache.delete_value(f"user|{self.user}")

		if self.has_value_changed("email"):
			create_account_on_agents(self.email, self.display_name, self.secret)
			return

		has_value_changed = self.has_value_changed("display_name") or self.has_value_changed("secret")
		if has_value_changed:
			patch_account_on_agents(
				self.email, self.display_name, self.secret, self.get_doc_before_save().secret
			)

	def on_trash(self) -> None:
		frappe.cache.delete_value(f"user|{self.user}")
		delete_account_from_agents(self.email)

	def validate_domain(self) -> None:
		"""Validates the domain."""

		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_user(self) -> None:
		"""Validates the user."""

		if not has_role(self.user, "Mailbox User"):
			frappe.throw(_("User {0} does not have Mailbox User role.").format(frappe.bold(self.user)))

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

	def generate_secret(self) -> None:
		"""Generates secret from password"""

		password = self.get_password("password")
		salt = crypt.mksalt(crypt.METHOD_SHA512)
		self.secret = crypt.crypt(password, salt)
