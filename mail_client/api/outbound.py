import json
from email.utils import parseaddr

import frappe
from frappe import _

from mail_client.mail_client.doctype.outgoing_mail.outgoing_mail import create_outgoing_mail


@frappe.whitelist(methods=["POST"])
def send(
	from_: str,
	to: str | list[str],
	subject: str,
	cc: str | list[str] | None = None,
	bcc: str | list[str] | None = None,
	html: str | None = None,
	reply_to: str | list[str] | None = None,
	in_reply_to_mail_type: str | None = None,
	in_reply_to_mail_name: str | None = None,
	custom_headers: dict | None = None,
	attachments: list[dict] | None = None,
) -> str:
	"""Send Mail."""

	display_name, sender = parseaddr(from_)
	doc = create_outgoing_mail(
		sender=sender,
		to=to,
		display_name=display_name,
		cc=cc,
		bcc=bcc,
		subject=subject,
		body_html=html,
		reply_to=reply_to,
		in_reply_to_mail_type=in_reply_to_mail_type,
		in_reply_to_mail_name=in_reply_to_mail_name,
		custom_headers=custom_headers,
		attachments=attachments,
		via_api=1,
	)

	return doc.name


@frappe.whitelist(methods=["POST"])
def send_raw(
	from_: str,
	to: str | list[str],
	raw_message: str,
) -> str:
	"""Send Raw Mail."""

	display_name, sender = parseaddr(from_)
	doc = create_outgoing_mail(
		sender=sender,
		to=to,
		display_name=display_name,
		raw_message=raw_message,
		via_api=1,
	)

	return doc.name


@frappe.whitelist(methods=["POST"])
def send_batch() -> list[str]:
	"""Send Mails in Batch."""

	mails = json.loads(frappe.request.data.decode())
	validate_batch(mails, mandatory_fields=["from_", "to", "subject"])

	documents = []
	for mail in mails:
		mail = get_mail_dict(mail)
		doc = create_outgoing_mail(**mail)
		documents.append(doc.name)

	return documents


@frappe.whitelist(methods=["POST"])
def send_raw_batch() -> list[str]:
	"""Send Raw Mails in Batch."""

	mails = json.loads(frappe.request.data.decode())
	validate_batch(mails, mandatory_fields=["from_", "to", "raw_message"])

	documents = []
	for mail in mails:
		mail = get_mail_dict(mail)
		doc = create_outgoing_mail(**mail)
		documents.append(doc.name)

	return documents


@frappe.whitelist(methods=["POST"])
def send_newsletter() -> None:
	"""Send Newsletter."""

	mails = json.loads(frappe.request.data.decode())

	if isinstance(mails, dict):
		mails = [mails]

	validate_batch(mails, mandatory_fields=["from_", "to"])

	for mail in mails:
		mail = get_mail_dict(mail)
		mail["is_newsletter"] = 1
		create_outgoing_mail(**mail)


def validate_batch(mails: list[dict], mandatory_fields: list[str]) -> None:
	"""Validates the batch data."""

	if len(mails) > 100:
		raise frappe.ValidationError("Batch size cannot exceed 100.")

	for mail in mails:
		for field in mandatory_fields:
			if not mail.get(field):
				raise frappe.ValidationError(f"{field} is mandatory.")


def get_mail_dict(data: dict) -> dict:
	"""Returns the mail dict."""

	display_name, sender = parseaddr(data["from_"])
	mail = {
		"sender": sender,
		"to": data["to"],
		"display_name": display_name,
		"via_api": 1,
	}

	if data.get("raw_message"):
		mail["raw_message"] = data["raw_message"]
	else:
		mail.update(
			{
				"subject": data["subject"],
				"cc": data.get("cc"),
				"bcc": data.get("bcc"),
				"body_html": data.get("html"),
				"reply_to": data.get("reply_to"),
				"custom_headers": data.get("headers"),
				"attachments": data.get("attachments"),
			}
		)

	return mail
