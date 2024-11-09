import re
from collections.abc import Callable
from datetime import datetime
from email.utils import parsedate_to_datetime as parsedate

import frappe
import pytz
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils import get_datetime, get_datetime_str, get_system_timezone
from frappe.utils.background_jobs import get_jobs
from frappe.utils.caching import request_cache


@request_cache
def convert_html_to_text(html: str) -> str:
	"""Returns plain text from HTML content."""

	text = ""

	if html:
		soup = BeautifulSoup(html, "html.parser")
		text = soup.get_text()
		text = re.sub(r"\s+", " ", text).strip()

	return text


def get_in_reply_to_mail(
	message_id: str | None = None,
) -> tuple[str, str] | tuple[None, None]:
	"""Returns mail type and name of the mail to which the given message is a reply to."""

	if message_id:
		for in_reply_to_mail_type in ["Outgoing Mail", "Incoming Mail"]:
			if in_reply_to_mail_name := frappe.db.get_value(
				in_reply_to_mail_type, {"message_id": message_id}, "name"
			):
				return in_reply_to_mail_type, in_reply_to_mail_name

	return None, None


def get_in_reply_to(
	in_reply_to_mail_type: str | None = None,
	in_reply_to_mail_name: str | None = None,
) -> str | None:
	"""Returns message_id of the mail to which the given mail is a reply to."""

	if in_reply_to_mail_type and in_reply_to_mail_name:
		return frappe.get_cached_value(in_reply_to_mail_type, in_reply_to_mail_name, "message_id")

	return None


def enqueue_job(method: str | Callable, **kwargs) -> None:
	"""Enqueues a background job."""

	site = frappe.local.site
	jobs = get_jobs(site=site)
	if not jobs or method not in jobs[site]:
		frappe.enqueue(method, **kwargs)


def convert_to_utc(date_time: datetime | str, from_timezone: str | None = None) -> "datetime":
	"""Converts the given datetime to UTC timezone."""

	dt = get_datetime(date_time)
	if dt.tzinfo is None:
		tz = pytz.timezone(from_timezone or get_system_timezone())
		dt = tz.localize(dt)

	return dt.astimezone(pytz.utc)


def parsedate_to_datetime(date_header: str, to_timezone: str | None = None) -> "datetime":
	"""Returns datetime object from parsed date header."""

	dt = parsedate(date_header)
	if not dt:
		frappe.throw(_("Invalid date format: {0}").format(date_header))

	return dt.astimezone(pytz.timezone(to_timezone or get_system_timezone()))


def parse_iso_datetime(
	datetime_str: str, to_timezone: str | None = None, as_str: bool = True
) -> str | datetime:
	"""Converts ISO datetime string to datetime object in given timezone."""

	if not to_timezone:
		to_timezone = get_system_timezone()

	dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00")).astimezone(pytz.timezone(to_timezone))

	return get_datetime_str(dt) if as_str else dt


def add_or_update_tzinfo(date_time: datetime | str, timezone: str | None = None) -> str:
	"""Adds or updates timezone to the datetime."""

	date_time = get_datetime(date_time)
	target_tz = pytz.timezone(timezone or get_system_timezone())

	if date_time.tzinfo is None:
		date_time = target_tz.localize(date_time)
	else:
		date_time = date_time.astimezone(target_tz)

	return str(date_time)
