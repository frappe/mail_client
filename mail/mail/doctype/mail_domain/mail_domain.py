# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from mail.mail_server import get_mail_server_domain_api
from mail.mail.doctype.mailbox.mailbox import create_postmaster_mailbox


class MailDomain(Document):
	def autoname(self) -> None:
		self.domain_name = self.domain_name.strip().lower()
		self.name = self.domain_name

	def validate(self) -> None:
		self.validate_newsletter_retention()

		if self.is_new():
			self.add_or_update_domain_in_mail_server()

		if not self.enabled:
			self.is_verified = 0

	def after_insert(self) -> None:
		create_postmaster_mailbox(self.domain_name)

	def validate_newsletter_retention(self) -> None:
		"""Validates the Newsletter Retention."""

		if self.newsletter_retention:
			if self.newsletter_retention < 1:
				frappe.throw(_("Newsletter Retention must be greater than 0."))

			max_newsletter_retention = frappe.db.get_single_value(
				"Mail Settings", "max_newsletter_retention", cache=True
			)
			if self.newsletter_retention > max_newsletter_retention:
				frappe.throw(
					_("Newsletter Retention must be less than or equal to {0}.").format(
						frappe.bold(max_newsletter_retention)
					)
				)
		else:
			self.newsletter_retention = frappe.db.get_single_value(
				"Mail Settings", "default_newsletter_retention", cache=True
			)

	def add_or_update_domain_in_mail_server(self) -> None:
		"""Adds or Updates the Domain in the Mail Server."""

		domain_api = get_mail_server_domain_api()
		response = domain_api.add_or_update_domain(self.domain_name, frappe.utils.get_url())

		for record in response["dns_records"]:
			self.append("dns_records", record)

		self.dkim_domain = response["dkim_domain"]
		self.dkim_selector = response["dkim_selector"]
		self.dkim_private_key = response["dkim_private_key"]

	@frappe.whitelist()
	def refresh_dns_records(self) -> None:
		"""Refreshes the DNS Records."""

		self.is_verified = 0
		self.dns_records.clear()

		domain_api = get_mail_server_domain_api()
		dns_records = domain_api.get_dns_records(self.domain_name)

		for record in dns_records:
			self.append("dns_records", record)

		self.save()

	@frappe.whitelist()
	def verify_dns_records(self, save: bool = True) -> None:
		"""Verifies the DNS Records."""

		domain_api = get_mail_server_domain_api()
		errors = domain_api.verify_dns_records(self.domain_name)

		if not errors:
			self.is_verified = 1
			frappe.msgprint(
				_("DNS Records verified successfully."), indicator="green", alert=True
			)
		else:
			self.is_verified = 0
			frappe.msgprint(
				errors, title="DNS Verification Failed", indicator="red", as_list=True
			)

		if save:
			self.save()
