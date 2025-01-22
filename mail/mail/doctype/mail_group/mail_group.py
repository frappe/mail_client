# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.mail.doctype.mail_agent_request_log.mail_agent_request_log import (
	create_group_on_agents,
	delete_group_from_agents,
	patch_group_on_agents,
)
from mail.utils.validation import (
	is_email_assigned,
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
)


class MailGroup(Document):
	def autoname(self) -> None:
		self.email = self.email.strip().lower()
		self.name = self.email

	def validate(self) -> None:
		self.validate_enabled()
		self.validate_domain()
		self.validate_email()

	def on_update(self) -> None:
		if self.enabled:
			if self.has_value_changed("enabled") or self.has_value_changed("email"):
				create_group_on_agents(self.email, self.display_name)
			elif self.has_value_changed("display_name"):
				patch_group_on_agents(self.email, self.display_name)
		elif self.has_value_changed("enabled"):
			delete_group_from_agents(self.email)

	def on_trash(self) -> None:
		if self.enabled:
			delete_group_from_agents(self.email)

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

		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_email(self) -> None:
		"""Validates the email address."""

		is_email_assigned(self.email, self.doctype, raise_exception=True)
		is_valid_email_for_domain(self.email, self.domain_name, raise_exception=True)
