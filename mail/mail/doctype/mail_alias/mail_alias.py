# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from mail.mail.doctype.mail_agent_job.mail_agent_job import (
	create_alias_on_agents,
	delete_alias_from_agents,
	patch_alias_on_agents,
)
from mail.utils.validation import (
	is_email_assigned,
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
)


class MailAlias(Document):
	def autoname(self) -> None:
		self.email = self.email.strip().lower()
		self.name = self.email

	def validate(self) -> None:
		self.validate_alias_for_name()
		self.validate_domain()
		self.validate_email()

	def on_update(self) -> None:
		if self.enabled:
			if self.has_value_changed("enabled") or self.has_value_changed("email"):
				create_alias_on_agents(self.alias_for_name, self.email)
			elif self.has_value_changed("alias_for_name"):
				patch_alias_on_agents(
					self.alias_for_name, self.get_doc_before_save().alias_for_name, self.email
				)
		elif self.has_value_changed("enabled"):
			delete_alias_from_agents(self.alias_for_name, self.email)

	def on_trash(self) -> None:
		if self.enabled:
			delete_alias_from_agents(self.alias_for_name, self.email)

	def validate_alias_for_name(self) -> None:
		"""Validates the alias for name."""

		if not frappe.db.get_value(self.alias_for_type, self.alias_for_name, "enabled"):
			frappe.throw(
				frappe._("The {0} {1} is disabled.").format(
					self.alias_for_type, frappe.bold(self.alias_for_name)
				)
			)

	def validate_domain(self) -> None:
		"""Validates the domain."""

		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_email(self) -> None:
		"""Validates the email address."""

		is_email_assigned(self.email, self.doctype, raise_exception=True)
		is_valid_email_for_domain(self.email, self.domain_name, raise_exception=True)
