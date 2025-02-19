import base64
import gzip
import os
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
from frappe.utils.caching import redis_cache, request_cache


def encode_image_to_base64(image_path: str) -> str:
	"""Encodes an image to a base64 string with line breaks every 76 characters."""

	image_path = os.path.abspath(image_path)
	with open(image_path, "rb") as image:
		image_base64 = base64.b64encode(image.read()).decode("utf-8")

	chunk_size = 76
	parts = [image_base64[i : i + chunk_size] for i in range(0, len(image_base64), chunk_size)]
	return "\n".join(parts)


def get_base64_image_data_uri(image_path: str) -> str:
	"""Generates a base64 data URI for an image."""

	image_base64 = encode_image_to_base64(image_path)
	image_format = image_path.split(".")[-1]
	return f"data:image/{image_format};base64,{image_base64}"


def generate_otp(length=5) -> int:
	"""Generates a random OTP."""

	lower_bound = 10 ** (length - 1)
	upper_bound = 10**length
	return int.from_bytes(os.urandom(length), byteorder="big") % (upper_bound - lower_bound) + lower_bound


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


def enqueue_job(method: str | Callable, deduplicate: bool = False, **kwargs) -> None:
	"""Enqueues a background job."""

	job_id = None
	if deduplicate:
		job_id = method.split(".")[-1] if isinstance(method, str) else method.__name__

	frappe.enqueue(method, job_id=job_id, deduplicate=deduplicate, **kwargs)


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

	from mail.utils.validation import validate_email_address

	return validate_email_address(email, check_mx=True, verify=True, smtp_timeout=10)


def remove_subaddressing(email: str) -> str:
	"""Removes subaddressing from an email address.

	Example:
	    input: "user+filter@example.com"
	    output: "user@example.com"
	"""
	match = re.match(r"([^+]+)(?:\+[^@]*)?(@.+)", email)
	return f"{match.group(1)}{match.group(2)}" if match else email


def normalize_email(email: str) -> str:
	"""Normalize email by removing dots before the @."""

	local, domain = email.split("@", 1)
	normalized_local = re.sub(r"\.", "", local)
	return f"{normalized_local}@{domain}"


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

	from mail.utils.cache import get_root_domain_name

	return f"dmarc@{get_root_domain_name()}"
