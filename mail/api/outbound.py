from email.utils import parseaddr

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import cint

from mail.mail.doctype.outgoing_mail.outgoing_mail import create_outgoing_mail


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=300, seconds=60)
def send(
	from_: str,
	subject: str,
	to: str | list[str] | None = None,
	cc: str | list[str] | None = None,
	bcc: str | list[str] | None = None,
	html: str | None = None,
	reply_to: str | list[str] | None = None,
	in_reply_to_mail_type: str | None = None,
	in_reply_to_mail_name: str | None = None,
	custom_headers: dict | None = None,
	attachments: list[dict] | None = None,
	is_newsletter: bool = False,
	do_not_submit: bool = False,
) -> str:
	"""Send Mail."""

	display_name, from_ = parseaddr(from_)
	doc = create_outgoing_mail(
		from_=from_,
		display_name=display_name,
		to=to,
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
		is_newsletter=cint(is_newsletter),
		do_not_submit=do_not_submit,
	)

	return doc.name


@frappe.whitelist(methods=["POST"])
@rate_limit(limit=300, seconds=60)
def send_raw(
	from_: str,
	to: str | list[str],
	raw_message: str | None = None,
	is_newsletter: bool = False,
) -> str:
	"""Send Raw Mail."""

	display_name, from_ = parseaddr(from_)
	raw_message = raw_message or get_message_from_files()
	if not raw_message:
		frappe.throw(_("The raw message is required."), frappe.MandatoryError)

	doc = create_outgoing_mail(
		from_=from_,
		to=to,
		display_name=display_name,
		raw_message=raw_message,
		via_api=1,
		is_newsletter=cint(is_newsletter),
	)

	return doc.name


def get_message_from_files() -> str | None:
	"""Returns the message from the files"""

	files = frappe._dict(frappe.request.files)

	if files and files.get("raw_message"):
		return files["raw_message"].read().decode("utf-8")
