# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from uuid_utils import uuid7


class MailRecipient(Document):
	def autoname(self) -> None:
		self.name = str(uuid7())


def on_doctype_update() -> None:
	frappe.db.add_unique(
		"Mail Recipient",
		["parent", "type", "email"],
		constraint_name="unique_parent_type_email",
	)
