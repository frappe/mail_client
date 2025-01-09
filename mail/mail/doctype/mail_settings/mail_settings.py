# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.core.api.file import get_max_file_size
from frappe.model.document import Document
from frappe.utils import cint

from mail.mail_server import MailServerAuthAPI


class MailSettings(Document):
	def validate(self) -> None:
		self.validate_mail_server()
		self.validate_outgoing_max_attachment_size()
		self.validate_outgoing_total_attachments_size()

	def validate_mail_server(self) -> None:
		"""Validates the Mail Server."""

		auth_api = MailServerAuthAPI(
			self.mail_server_host,
			self.mail_server_api_key,
			self.get_password("mail_server_api_secret"),
		)
		auth_api.validate()

	def validate_outgoing_max_attachment_size(self) -> None:
		"""Validates the Outgoing Max Attachment Size."""

		max_file_size = cint(get_max_file_size() / 1024 / 1024)

		if self.outgoing_max_attachment_size > max_file_size:
			frappe.throw(
				_("{0} should be less than or equal to {1} MB.").format(
					frappe.bold("Max Attachment Size"), frappe.bold(max_file_size)
				)
			)

	def validate_outgoing_total_attachments_size(self) -> None:
		"""Validates the Outgoing Total Attachments Size."""

		if self.outgoing_max_attachment_size > self.outgoing_total_attachments_size:
			frappe.throw(
				_("{0} should be greater than or equal to {1}.").format(
					frappe.bold("Total Attachments Size"), frappe.bold("Max Attachment Size")
				)
			)


def validate_mail_settings() -> None:
	"""Validates the mandatory fields in the Mail Settings."""

	client_settings = frappe.get_doc("Mail Settings")
	mandatory_fields = [
		"mail_server_host",
		"mail_server_api_key",
		"mail_server_api_secret",
	]

	for field in mandatory_fields:
		if not client_settings.get(field):
			field_label = frappe.get_meta("Mail Settings").get_label(field)
			frappe.throw(_("Please set the {0} in the Mail Settings.").format(frappe.bold(field_label)))
