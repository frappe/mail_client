# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from mail.mail.doctype.mail_agent_job.mail_agent_job import (
	create_group_on_agents,
	delete_group_from_agents,
	patch_group_on_agents,
)
from mail.utils.validation import (
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
)


class MailGroup(Document):
	def autoname(self) -> None:
		self.email = self.email.strip().lower()
		self.name = self.email

	def validate(self) -> None:
		self.validate_domain()
		self.validate_email()
		self.validate_display_name()

	def on_update(self) -> None:
		if self.has_value_changed("email"):
			create_group_on_agents(self.email, self.display_name)
			return

		has_value_changed = self.has_value_changed("display_name")
		if has_value_changed:
			patch_group_on_agents(self.email, self.display_name)

	def on_trash(self) -> None:
		delete_group_from_agents(self.email)

	def validate_domain(self) -> None:
		"""Validates the domain."""

		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_email(self) -> None:
		"""Validates the email address."""

		is_valid_email_for_domain(self.email, self.domain_name, raise_exception=True)

	def validate_display_name(self) -> None:
		"""Validates the display name."""

		if self.is_new() and not self.display_name:
			self.display_name = frappe.db.get_value("User", self.user, "full_name")
