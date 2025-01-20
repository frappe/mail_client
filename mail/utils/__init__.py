import gzip
import re
import secrets
import string
import zipfile
from collections.abc import Callable
from io import BytesIO
from typing import Literal

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils.background_jobs import get_jobs
from frappe.utils.caching import redis_cache, request_cache

from mail.utils.cache import get_root_domain_name
from mail.utils.validation import validate_email_address


def generate_secret(length: int = 32):
	"""Generates a random secret key."""

	characters = string.ascii_letters + string.digits
	return "".join(secrets.choice(characters) for _ in range(length))


def load_compressed_file(file_path: str | None = None, file_data: bytes | None = None) -> str:
	"""Load content from a compressed file or bytes object."""

	if not file_path and not file_data:
		frappe.throw(_("Either file path or file data is required."))

	if file_path:
		if zipfile.is_zipfile(file_path):
			with zipfile.ZipFile(file_path, "r") as zip_file:
				file_name = zip_file.namelist()[0]
				with zip_file.open(file_name) as file:
					content = file.read().decode()
					return content
		else:
			with gzip.open(file_path, "rt") as gz_file:
				return gz_file.read()

	elif file_data:
		try:
			with zipfile.ZipFile(BytesIO(file_data), "r") as zip_file:
				file_name = zip_file.namelist()[0]
				with zip_file.open(file_name) as file:
					return file.read().decode()
		except zipfile.BadZipFile:
			pass

		try:
			with gzip.open(BytesIO(file_data), "rt") as gz_file:
				return gz_file.read()
		except OSError:
			pass

		frappe.throw(_("Failed to load content from the compressed file."))


def enqueue_job(method: str | Callable, **kwargs) -> None:
	"""Enqueues a background job."""

	site = frappe.local.site
	jobs = get_jobs(site=site)
	if not jobs or method not in jobs[site]:
		frappe.enqueue(method, **kwargs)


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


@frappe.whitelist()
@redis_cache(ttl=3600)
def check_deliverability(email: str) -> bool:
	"""Wrapper function of `utils.validation.validate_email_address` for caching."""

	return validate_email_address(email, check_mx=True, verify=True, smtp_timeout=10)


def get_dkim_host(domain_name: str, type: Literal["rsa", "ed25519"]) -> str:
	"""
	Returns DKIM host.
	e.g. example-com-r for RSA and example-com-e for Ed25519.
	"""

	return f"{domain_name.replace('.', '-')}-{type[0]}"


def get_dkim_selector(key_type: Literal["rsa", "ed25519"]) -> str:
	"""
	Returns DKIM selector.
	e.g. frappemail-r for RSA and frappemail-e for Ed25519.
	"""

	return f"frappemail-{key_type[0]}"


def get_dmarc_address() -> str:
	"""
	Returns DMARC address.
	e.g. dmarc@rootdomain.com
	"""

	return f"dmarc@{get_root_domain_name()}"
