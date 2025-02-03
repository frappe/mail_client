# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MailRecipient(Document):
	pass


def on_doctype_update() -> None:
	frappe.db.add_unique(
		"Mail Recipient",
		["parent", "type", "email"],
		constraint_name="unique_parent_type_email",
	)
