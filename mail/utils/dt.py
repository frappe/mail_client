from datetime import datetime, timezone
from email.utils import parsedate_to_datetime as parsedate
from zoneinfo import ZoneInfo

import frappe
from frappe import _
from frappe.utils import convert_utc_to_system_timezone, get_datetime, get_datetime_str, get_system_timezone


def convert_to_utc(date_time: datetime | str, from_timezone: str | None = None) -> "datetime":
	"""Converts the given datetime to UTC timezone."""

	dt = get_datetime(date_time)
	if dt.tzinfo is None:
		tz = ZoneInfo(from_timezone or get_system_timezone())
		dt = dt.replace(tzinfo=tz)

	return dt.astimezone(timezone.utc)


def parsedate_to_datetime(date_header: str) -> "datetime":
	"""Returns datetime object from parsed date header."""

	utc_dt = parsedate(date_header)
	if not utc_dt:
		frappe.throw(_("Invalid date format: {0}").format(date_header))

	return convert_utc_to_system_timezone(utc_dt)


def parse_iso_datetime(
	datetime_str: str, to_timezone: str | None = None, as_str: bool = True
) -> str | datetime:
	"""Converts ISO datetime string to datetime object in given timezone."""

	if not to_timezone:
		to_timezone = get_system_timezone()

	dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00")).astimezone(ZoneInfo(to_timezone))

	return get_datetime_str(dt) if as_str else dt


def add_or_update_tzinfo(date_time: datetime | str, timezone: str | None = None) -> str:
	"""Adds or updates timezone to the datetime."""

	date_time = get_datetime(date_time)
	target_tz = ZoneInfo(timezone or get_system_timezone())

	if date_time.tzinfo is None:
		date_time = date_time.replace(tzinfo=target_tz)
	else:
		date_time = date_time.astimezone(target_tz)

	return str(date_time)
