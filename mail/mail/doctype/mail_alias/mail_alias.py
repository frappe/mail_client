# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from mail.utils.validation import (
	validate_domain_is_enabled_and_verified,
	is_valid_email_for_domain,
	validate_mailbox_for_incoming,
)


class MailAlias(Document):
	def autoname(self) -> None:
		self.alias = self.alias.strip().lower()
		self.name = self.alias

	def validate(self) -> None:
		self.validate_domain()
		self.validate_alias()
		self.validate_mailboxes()

	def validate_domain(self) -> None:
		"""Validates the domain."""

		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_alias(self) -> None:
		"""Validates the alias."""

		is_valid_email_for_domain(self.alias, self.domain_name, raise_exception=True)

	def validate_mailboxes(self) -> None:
		"""Validates the mailboxes."""

		mailboxes = []

		for mailbox in self.mailboxes:
			if mailbox.mailbox == self.alias:
				frappe.throw(
					_("Row #{0}: Mailbox cannot be the same as the alias.").format(mailbox.idx)
				)
			elif mailbox.mailbox in mailboxes:
				frappe.throw(
					_("Row #{0}: Duplicate mailbox {1}.").format(
						mailbox.idx, frappe.bold(mailbox.mailbox)
					)
				)

			validate_mailbox_for_incoming(mailbox.mailbox)
			mailboxes.append(mailbox.mailbox)
