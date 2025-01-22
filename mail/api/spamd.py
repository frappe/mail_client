from html import unescape
from typing import Literal

import frappe
from frappe import _

from mail.mail.doctype.spam_check_log.spam_check_log import create_spam_check_log


@frappe.whitelist(methods=["POST"])
def scan(message: str | None = None) -> dict:
	"""Returns the spam score, spamd response and scanning mode of the message"""

	message = message or get_message_from_files()
	if not message:
		frappe.throw(_("The message is required."), frappe.MandatoryError)

	message = get_unescaped_message(message)
	spam_log = create_spam_check_log(message)
	return {
		"spam_score": spam_log.spam_score,
		"spamd_response": spam_log.spamd_response,
		"scanning_mode": spam_log.scanning_mode,
	}


@frappe.whitelist(methods=["POST"])
def is_spam(message: str | None = None, message_type: Literal["Outbound"] = "Outbound") -> bool:
	"""Returns True if the message is spam else False"""

	message = message or get_message_from_files()
	if not message:
		frappe.throw(_("The message is required."), frappe.MandatoryError)

	message = get_unescaped_message(message)
	spam_log = create_spam_check_log(message)
	return spam_log.is_spam(message_type)


@frappe.whitelist(methods=["POST"])
def get_spam_score(message: str | None = None) -> float:
	"""Returns the spam score of the message"""

	message = message or get_message_from_files()
	if not message:
		frappe.throw(_("The message is required."), frappe.MandatoryError)

	message = get_unescaped_message(message)
	spam_log = create_spam_check_log(message)
	return spam_log.spam_score


def get_message_from_files() -> str | None:
	"""Returns the message from the files"""

	files = frappe._dict(frappe.request.files)

	if files and files.get("message"):
		return files["message"].read().decode("utf-8")


def get_unescaped_message(message: str | bytes) -> str:
	"""Returns the unescaped message"""

	if isinstance(message, bytes):
		message = message.decode("utf-8")

	return unescape(message)
