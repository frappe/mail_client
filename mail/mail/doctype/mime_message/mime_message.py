# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from uuid_utils import uuid7


class MIMEMessage(Document):
	def autoname(self) -> None:
		self.name = str(uuid7())


def create_mime_message(message: str | bytes | None = None) -> str | None:
	"""Creates a MIME Message document from the given message"""

	if not message:
		return

	if isinstance(message, bytes):
		message = message.decode("utf-8")

	doc = frappe.new_doc("MIME Message")
	doc.message = message
	doc.insert(ignore_permissions=True)

	return doc.name


def update_mime_message(name: str | None = None, message: str | bytes | None = None) -> None:
	"""Updates the message of the MIME Message document"""

	if not name or not message:
		return

	if isinstance(message, bytes):
		message = message.decode("utf-8")

	doc = frappe.get_doc("MIME Message", name)
	doc.message = message
	doc.save(ignore_permissions=True)


def get_mime_message(name: str, raise_exception: bool = True) -> str | None:
	"""Returns the message of the MIME Message document"""

	message = frappe.db.get_value("MIME Message", name, "message")

	if not message and raise_exception:
		frappe.throw(_("MIME Message {0} not found.").format(frappe.bold(name)))

	return message
