from datetime import datetime, timezone
from email.utils import formataddr
from typing import TYPE_CHECKING

import frappe
from frappe import _
from frappe.utils import convert_utc_to_system_timezone, now

from mail.api.auth import validate_account, validate_user
from mail.mail.doctype.mail_sync_history.mail_sync_history import get_mail_sync_history
from mail.utils.dt import convert_to_utc

if TYPE_CHECKING:
	from mail.mail.doctype.mail_sync_history.mail_sync_history import MailSyncHistory


@frappe.whitelist(methods=["GET"])
def pull(
	account: str,
	limit: int = 50,
	last_synced_at: str | None = None,
) -> dict[str, list[dict] | str]:
	"""Returns the emails for the given mail account."""

	validate_user()
	validate_account(account)
	validate_max_sync_limit(limit)

	result = []
	source = get_source()
	last_synced_at = convert_to_system_timezone(last_synced_at)
	sync_history = get_mail_sync_history(source, frappe.session.user, account)
	result = get_incoming_mails(account, limit, last_synced_at or sync_history.last_synced_at)
	update_mail_sync_history(sync_history, result["last_synced_at"], result["last_synced_mail"])
	result["last_synced_at"] = convert_to_utc(result["last_synced_at"])

	return result


@frappe.whitelist(methods=["GET"])
def pull_raw(
	account: str,
	limit: int = 50,
	last_synced_at: str | None = None,
) -> dict[str, list[str] | str]:
	"""Returns the raw-emails for the given mail account."""

	validate_user()
	validate_account(account)
	validate_max_sync_limit(limit)

	result = []
	source = get_source()
	last_synced_at = convert_to_system_timezone(last_synced_at)
	sync_history = get_mail_sync_history(source, frappe.session.user, account)
	result = get_raw_incoming_mails(account, limit, last_synced_at or sync_history.last_synced_at)
	update_mail_sync_history(sync_history, result["last_synced_at"], result["last_synced_mail"])
	result["last_synced_at"] = convert_to_utc(result["last_synced_at"])

	return result


def validate_max_sync_limit(limit: int) -> None:
	"""Validates if the limit is within the maximum limit."""

	max_sync_limit = 100

	if limit > max_sync_limit:
		frappe.throw(_("Cannot fetch more than {0} emails at a time.").format(max_sync_limit))


def convert_to_system_timezone(last_synced_at: str) -> datetime | None:
	"""Converts the last_synced_at to system timezone."""

	if last_synced_at:
		dt = datetime.fromisoformat(last_synced_at)
		dt_utc = dt.astimezone(timezone.utc)
		return convert_utc_to_system_timezone(dt_utc)


def get_source() -> str:
	"""Returns the source of the request."""

	return frappe.request.headers.get("X-Site") or frappe.local.request_ip


def get_incoming_mails(
	account: str,
	limit: int,
	last_synced_at: str | None = None,
) -> dict[str, list[dict] | str]:
	"""Returns the incoming mails for the given mail account."""

	IM = frappe.qb.DocType("Incoming Mail")
	query = (
		frappe.qb.from_(IM)
		.select(
			IM.processed_at,
			IM.name.as_("id"),
			IM.folder,
			IM.display_name,
			IM.sender,
			IM.created_at,
			IM.subject,
			IM.body_html.as_("html"),
			IM.body_plain.as_("text"),
			IM.reply_to,
		)
		.where((IM.docstatus == 1) & (IM.receiver == account))
		.orderby(IM.processed_at)
		.limit(limit)
	)

	if last_synced_at:
		query = query.where(IM.processed_at > last_synced_at)

	mails = query.run(as_dict=True)
	last_synced_at = mails[-1].processed_at if mails else now()
	last_synced_mail = mails[-1].id if mails else None

	for mail in mails:
		mail.pop("processed_at")
		mail["from"] = formataddr((mail.pop("display_name"), mail.pop("sender")))
		mail["to"], mail["cc"] = get_recipients(mail)
		mail["created_at"] = convert_to_utc(mail.created_at)

	return {
		"mails": mails,
		"last_synced_at": last_synced_at,
		"last_synced_mail": last_synced_mail,
	}


def get_raw_incoming_mails(
	account: str,
	limit: int,
	last_synced_at: str | None = None,
) -> dict[str, list[str] | str]:
	"""Returns the raw incoming mails for the given mail account."""

	IM = frappe.qb.DocType("Incoming Mail")
	query = (
		frappe.qb.from_(IM)
		.select(IM.processed_at, IM.name.as_("id"), IM._message)
		.where((IM.docstatus == 1) & (IM.receiver == account))
		.orderby(IM.processed_at)
		.limit(limit)
	)

	if last_synced_at:
		query = query.where(IM.processed_at > last_synced_at)

	data = query.run(as_dict=True)

	if not data:
		return {
			"mails": [],
			"last_synced_at": now(),
			"last_synced_mail": None,
		}

	MIME = frappe.qb.DocType("MIME Message")
	mails = (
		frappe.qb.from_(MIME).select(MIME.message).where(MIME.name.isin([d._message for d in data]))
	).run(pluck="message")
	return {
		"mails": mails,
		"last_synced_at": data[-1].processed_at,
		"last_synced_mail": data[-1].id,
	}


def update_mail_sync_history(
	sync_history: "MailSyncHistory",
	last_synced_at: str,
	last_synced_mail: str | None = None,
) -> None:
	"""Update the last_synced_at in the Mail Sync History."""

	kwargs = {
		"last_synced_at": last_synced_at or now(),
	}

	if last_synced_mail:
		kwargs["last_synced_mail"] = last_synced_mail

	frappe.db.set_value(sync_history.doctype, sync_history.name, kwargs)
	frappe.db.commit()


def get_recipients(mail: dict) -> tuple[list[str], list[str]]:
	"""Returns the recipients for the given mail."""

	to, cc = [], []
	recipients = frappe.db.get_all(
		"Mail Recipient",
		filters={"parenttype": "Incoming Mail", "parent": mail.id},
		fields=["type", "display_name", "email"],
	)

	for recipient in recipients:
		if recipient.type == "To":
			to.append(formataddr((recipient.display_name, recipient.email)))
		elif recipient.type == "Cc":
			cc.append(formataddr((recipient.display_name, recipient.email)))

	return to, cc
