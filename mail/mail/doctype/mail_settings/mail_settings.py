# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MailSettings(Document):
	pass


def validate_mail_settings() -> None:
	"""Validates the mandatory fields in the Mail Settings."""

	mail_settings = frappe.get_doc("Mail Settings")
	mandatory_fields = [
		"root_domain_name",
		"spf_host",
		"default_ttl",
	]

	for field in mandatory_fields:
		if not mail_settings.get(field):
			field_label = frappe.get_meta("Mail Settings").get_label(field)
			frappe.throw(_("Please set the {0} in the Mail Settings.").format(frappe.bold(field_label)))
