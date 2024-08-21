import json
import frappe
from email.utils import parseaddr
from mail.utils.user import get_user_mailboxes
from mail.config.constants import NEWSLETTER_STREAM
from frappe.utils.background_jobs import get_redis_connection_without_auth
from mail.mail.doctype.outgoing_mail.outgoing_mail import create_outgoing_mail


@frappe.whitelist(methods=["POST"])
def send(
	from_: str,
	to: str | list[str],
	subject: str,
	cc: str | list[str] | None = None,
	bcc: str | list[str] | None = None,
	raw_html: str | None = None,
	reply_to: str | list[str] | None = None,
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
		raw_html=raw_html,
		reply_to=reply_to,
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

	user = frappe.session.user
	rclient = get_redis_connection_without_auth()
	for mail in mails:
		mail = get_mail_dict(mail)

		if mail["sender"] not in get_user_mailboxes(user, "Outgoing"):
			from mail.utils.cache import get_user_default_mailbox

			mail["sender"] = get_user_default_mailbox(user)

		rclient.xadd(NEWSLETTER_STREAM, mail)


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
				"raw_html": data.get("html"),
				"reply_to": data.get("reply_to"),
				"custom_headers": data.get("headers"),
				"attachments": data.get("attachments"),
			}
		)

	return mail
