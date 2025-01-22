import re
from email import message_from_string, policy
from email.header import decode_header, make_header
from email.utils import parseaddr
from typing import TYPE_CHECKING
from urllib.parse import unquote

from frappe.utils import cint, get_datetime_str
from frappe.utils.file_manager import save_file

from mail.utils.dt import parsedate_to_datetime

if TYPE_CHECKING:
	from email.message import Message


class EmailParser:
	def __init__(self, message: str) -> None:
		self.message = self.get_parsed_message(message)
		self.content_id_and_file_url_map = {}

	@staticmethod
	def get_parsed_message(message: str) -> "Message":
		"""Returns parsed email message object from string."""

		return message_from_string(message)

	def get_message_id(self) -> str | None:
		"""Returns the message ID of the email."""

		if message_id := self.message.get("Message-ID"):
			return remove_whitespace_characters(message_id)

	def get_in_reply_to(self) -> str | None:
		"""Returns the in-reply-to message ID of the email."""

		if in_reply_to := self.message.get("In-Reply-To"):
			return remove_whitespace_characters(in_reply_to)

	def get_subject(self) -> str | None:
		"""Returns the decoded subject of the email."""

		if subject := self.message["Subject"]:
			decoded_subject = str(make_header(decode_header(subject)))
			return remove_whitespace_characters(decoded_subject)

		return None

	def get_sender(self) -> tuple[str, str]:
		"""Returns the display name and email of the sender."""

		return parseaddr(self.message["From"])

	def get_reply_to(self) -> str:
		"""Returns the reply-to email(s) of the email."""

		if reply_to := self.message.get("Reply-To"):
			return remove_whitespace_characters(reply_to)

	def get_priority(self) -> int:
		"""Returns the priority of the email."""

		return cint(self.get_header("X-Priority"))

	def get_header(self, header: str) -> str | None:
		"""Returns the value of the header."""

		return self.message[header]

	def update_header(self, header: str, value: str) -> None:
		"""Updates the value of the header."""

		if header in self.message:
			del self.message[header]

		self.message[header] = value

	def get_date(self) -> str | None:
		"""Returns the date of the email."""

		if date_header := self.message.get("Date"):
			return get_datetime_str(parsedate_to_datetime(date_header))

	def get_size(self) -> int:
		"""Returns the size of the email."""

		return len(self.message.as_string(policy=policy.default).encode("utf-8"))

	def get_recipients(self, types: str | list | None = None) -> list[dict]:
		"""Returns the list of recipients of the email."""

		if not types:
			types = ["To", "Cc", "Bcc"]
		elif isinstance(types, str):
			types = [types]

		recipients = []
		for type in types:
			if addresses := self.message.get(type):
				for address in addresses.split(","):
					display_name, email = parseaddr(remove_whitespace_characters(address))
					if email:
						recipients.append({"type": type, "email": email, "display_name": display_name})

		return recipients

	def save_attachments(self, doctype: str, docname: str, is_private: bool = True) -> None:
		"""Saves the attachments of the email."""

		def save_attachment(
			filename: str, content: bytes, doctype: str, docname: str, is_private: bool
		) -> dict:
			"""Saves the attachment as a file."""

			kwargs = {
				"fname": filename,
				"content": content,
				"df": "file",
				"dt": doctype,
				"dn": docname,
				"is_private": cint(is_private),
			}
			file = save_file(**kwargs)
			return {
				"name": file.name,
				"file_name": file.file_name,
				"file_url": file.file_url,
				"is_private": file.is_private,
			}

		for part in self.message.walk():
			filename = part.get_filename()
			disposition = part.get("Content-Disposition")

			if disposition and filename:
				filename = unquote(filename)
				disposition = disposition.lower()

				if disposition.startswith("inline"):
					if content_id := re.sub(r"[<>]", "", part.get("Content-ID", "")):
						if payload := part.get_payload(decode=True):
							file = save_attachment(filename, payload, doctype, docname, is_private)
							self.content_id_and_file_url_map[content_id] = file["file_url"]

				elif disposition.startswith("attachment"):
					if payload := part.get_payload(decode=True):
						save_attachment(filename, payload, doctype, docname, is_private)

	def get_body(self) -> tuple[str | None, str | None]:
		"""Returns the HTML and plain text body of the email."""

		body_html, body_plain = "", ""

		for part in self.message.walk():
			content_type = part.get_content_type()

			if content_type == "text/html":
				if payload := part.get_payload(decode=True):
					charset = part.get_content_charset() or "utf-8"
					body_html += payload.decode(charset, "ignore")

			elif content_type == "text/plain":
				if payload := part.get_payload(decode=True):
					charset = part.get_content_charset() or "utf-8"
					body_plain += payload.decode(charset, "ignore")

		if self.content_id_and_file_url_map:
			for content_id, file_url in self.content_id_and_file_url_map.items():
				body_html = body_html.replace(f"cid:{content_id}", file_url)
				body_plain = body_plain.replace(f"cid:{content_id}", file_url)

		return body_html or None, body_plain or None

	def get_authentication_results(self) -> dict[str, int | str]:
		"""Returns the authentication results of the email."""

		result = {}
		checks = ["spf", "dkim", "dmarc"]

		for check in checks:
			result[f"{check}_pass"] = 0
			result[f"{check}_description"] = "Header not found."

		if headers := self.message.get_all("Authentication-Results"):
			if len(headers) == 1:
				headers = headers[0].split(";")

			for header in headers:
				header = remove_whitespace_characters(header)
				header_lower = header.lower()

				for check in checks:
					if f"{check}=" in header_lower:
						result[f"{check}_pass"] = 1 if f"{check}=pass" in header_lower else 0
						result[f"{check}_description"] = header
						break

		return result

	def get_message(self) -> str:
		"""Returns the email message as a string."""

		return self.message.as_string()


def remove_whitespace_characters(text: str) -> str:
	"""Removes whitespace characters from the text."""

	return text.replace("\t", "").replace("\r", "").replace("\n", "").strip()


def extract_ip_and_host(header: str | None = None) -> tuple[str | None, str | None]:
	"""Extracts the IP and Host from the given `Received` header."""

	if not header:
		return None, None

	ip_pattern = re.compile(r"\[(?P<ip>[\d\.]+|[a-fA-F0-9:]+)")
	host_pattern = re.compile(r"from\s+(?P<host>[^\s]+)")

	ip_match = ip_pattern.search(header)
	ip = ip_match.group("ip") if ip_match else None

	host_match = host_pattern.search(header)
	host = host_match.group("host") if host_match else None

	return ip, host


def extract_spam_status(header: str | None = None) -> tuple[bool, float]:
	"""
	Extracts the spam status and score from the given `X-Spam-Status` header.

	Args:
	    header (str | None): The `X-Spam-Status` header.

	Returns:
	    Tuple[bool, float]: A tuple containing the spam status (True for "Yes", False otherwise) and the spam score.
	"""

	if not header:
		return False, 0.0

	status_pattern = re.compile(r"^\s*(Yes|No)", re.IGNORECASE)
	score_pattern = re.compile(r"score=(-?\d+\.?\d*)")

	status_match = status_pattern.search(header)
	score_match = score_pattern.search(header)

	status = status_match.group(1).lower() == "yes" if status_match else False
	score = float(score_match.group(1)) if score_match else 0.0

	return status, score
