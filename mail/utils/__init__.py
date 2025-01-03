import re
import secrets
import socket
import string
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime as parsedate
from zoneinfo import ZoneInfo

import dns.resolver
import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils import convert_utc_to_system_timezone, get_datetime, get_datetime_str, get_system_timezone
from frappe.utils.background_jobs import get_jobs
from frappe.utils.caching import request_cache


def get_dns_record(fqdn: str, type: str = "A", raise_exception: bool = False) -> dns.resolver.Answer | None:
	"""Returns DNS record for the given FQDN and type."""

	err_msg = None

	try:
		resolver = dns.resolver.Resolver(configure=False)
		resolver.nameservers = [
			"1.1.1.1",
			"8.8.4.4",
			"8.8.8.8",
			"9.9.9.9",
		]

		r = resolver.resolve(fqdn, type)
		return r
	except dns.resolver.NXDOMAIN:
		err_msg = _("{0} does not exist.").format(frappe.bold(fqdn))
	except dns.resolver.NoAnswer:
		err_msg = _("No answer for {0}.").format(frappe.bold(fqdn))
	except dns.exception.DNSException as e:
		err_msg = _(str(e))

	if raise_exception and err_msg:
		frappe.throw(err_msg)


def get_host_by_ip(ip_address: str, raise_exception: bool = False) -> str | None:
	"""Returns host for the given IP address."""

	err_msg = None

	try:
		return socket.gethostbyaddr(ip_address)[0]
	except Exception as e:
		err_msg = _(str(e))

	if raise_exception and err_msg:
		frappe.throw(err_msg)


def verify_dns_record(fqdn: str, type: str, expected_value: str, debug: bool = False) -> bool:
	"""Verifies the DNS Record."""

	if result := get_dns_record(fqdn, type):
		for data in result:
			if data:
				if type == "MX":
					data = data.exchange
				data = data.to_text().replace('"', "")
				if type == "TXT" and "._domainkey." in fqdn:
					data = data.replace(" ", "")
					expected_value = expected_value.replace(" ", "")
				if data == expected_value:
					return True
			if debug:
				frappe.msgprint(f"Expected: {expected_value} Got: {data}")
	return False


def generate_secret(length: int = 32):
	"""Generates a random secret key."""

	characters = string.ascii_letters + string.digits
	return "".join(secrets.choice(characters) for _ in range(length))


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
