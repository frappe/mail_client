# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import random
from email import policy
from email.encoders import encode_base64
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid, parseaddr
from mimetypes import guess_type
from re import finditer
from urllib.parse import parse_qs, urlparse

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import Interval, Order
from frappe.query_builder.functions import Now
from frappe.utils import (
	add_to_date,
	cint,
	flt,
	get_datetime_str,
	now,
	random_string,
	time_diff_in_seconds,
	validate_email_address,
)
from frappe.utils.file_manager import save_file
from uuid_utils import uuid7

from mail.mail.doctype.bounce_log.bounce_log import is_email_blocked
from mail.mail.doctype.mail_contact.mail_contact import create_mail_contact
from mail.mail.doctype.mime_message.mime_message import (
	create_mime_message,
	get_mime_message,
	update_mime_message,
)
from mail.mail.doctype.spam_check_log.spam_check_log import create_spam_check_log
from mail.smtp import SMTPContext
from mail.utils import (
	convert_html_to_text,
	get_in_reply_to,
	get_in_reply_to_mail,
)
from mail.utils.cache import get_account_for_email, get_account_for_user, get_default_outgoing_email_for_user
from mail.utils.dns import get_host_by_ip
from mail.utils.dt import parsedate_to_datetime
from mail.utils.email_parser import EmailParser
from mail.utils.user import get_user_email_addresses, is_account_owner, is_system_manager

MAX_FAILED_COUNT = 5


class OutgoingMail(Document):
	@property
	def raw_message(self) -> str | None:
		if self._raw_message:
			return get_mime_message(self._raw_message)

	@raw_message.setter
	def raw_message(self, value: str | bytes) -> None:
		if self._raw_message:
			update_mime_message(self._raw_message, value)
		else:
			self._raw_message = create_mime_message(value)

	@property
	def message(self) -> str | None:
		if self._message:
			return get_mime_message(self._message)

	@message.setter
	def message(self, value: str | bytes) -> None:
		if self._message:
			update_mime_message(self._message, value)
		else:
			self._message = create_mime_message(value)

	def autoname(self) -> None:
		self.name = str(uuid7())

	def validate(self) -> None:
		self.validate_amended_doc()
		self.set_folder()
		self.set_priority()
		self.set_token()
		self.validate_from_()
		self.set_sender()
		self.set_domain_name()
		self.load_runtime()
		self.validate_domain_name()
		self.validate_sender()
		self.set_display_name()
		self.set_reply_to()
		self.validate_in_reply_to()
		self.validate_recipients()
		self.validate_custom_headers()
		self.load_attachments()
		self.validate_attachments()
		self.validate_include_agent_groups()
		self.validate_exclude_agent_groups()
		self.validate_include_agents()
		self.validate_exclude_agents()

		if self.get("_action") == "submit":
			self.set_ip_address()
			self.set_message_id()

			if not self.raw_message:
				self.set_body_html()
				self.set_body_plain()

			self.generate_message()
			self.validate_max_message_size()

	def on_submit(self) -> None:
		self.create_mail_contacts()

		if not self.is_newsletter:
			if self.via_api and self.submitted_after <= 5:
				self._db_set(priority=1)
				self.process_for_delivery()
		else:
			self._db_set(status="Pending", notify_update=True)

	def on_update_after_submit(self) -> None:
		self.set_folder()

	def on_trash(self) -> None:
		if self.docstatus != 0 and frappe.session.user != "Administrator":
			frappe.throw(_("Only Administrator can delete Outgoing Mail."))

	def validate_amended_doc(self) -> None:
		"""Validates the amended document."""

		if self.amended_from:
			frappe.throw(_("Amending {0} is not allowed.").format(frappe.bold("Outgoing Mail")))

	def set_folder(self) -> None:
		"""Validates the folder"""

		folder = self.folder
		if self.docstatus == 0:
			folder = "Drafts"
		elif folder == "Drafts":
			folder = "Sent"

		if self.get("_action") == "update_after_submit":
			self._db_set(folder=folder, notify_update=True)
		else:
			self.folder = folder

	def set_priority(self) -> None:
		"""Sets the priority."""

		self.priority = -1 if self.is_newsletter else 0

	def set_token(self):
		"""Sets the token."""

		if not self.token:
			self.token = random_string(10)

	def validate_from_(self) -> None:
		"""Validates the from address."""

		user = frappe.session.user

		if is_system_manager(user):
			return

		if self.from_ not in get_user_email_addresses(user):
			frappe.throw(_("You are not allowed to send from address {0}.").format(frappe.bold(self.from_)))

	def set_sender(self) -> None:
		"""Sets the sender."""

		account = (
			get_account_for_email(self.from_)
			if is_system_manager(frappe.session.user)
			else get_account_for_user(frappe.session.user)
		)

		if not account:
			if is_system_manager(frappe.session.user):
				frappe.throw(_("No Mail Account found for email {0}.").format(frappe.bold(self.from_)))

			frappe.throw(_("No Mail Account found for user {0}.").format(frappe.bold(frappe.session.user)))

		self.sender = account

	def set_domain_name(self) -> None:
		"""Sets the domain name."""

		self.domain_name = self.from_.split("@", 1)[1]

	def load_runtime(self) -> None:
		"""Loads the runtime properties."""

		self.runtime = frappe._dict()
		self.runtime.mail_settings = frappe.get_cached_doc("Mail Settings")
		self.runtime.mail_account = frappe.get_cached_doc("Mail Account", self.sender)
		self.runtime.mail_domain = frappe.get_cached_doc("Mail Domain", self.domain_name)

	def validate_domain_name(self) -> None:
		"""Validates the domain name."""

		if not self.runtime.mail_domain.enabled:
			frappe.throw(_("Mail Domain {0} is disabled.").format(frappe.bold(self.domain_name)))
		if not self.runtime.mail_domain.is_verified:
			frappe.throw(_("Mail Domain {0} is not verified.").format(frappe.bold(self.domain_name)))

	def validate_sender(self) -> None:
		"""Validates the sender."""

		user = frappe.session.user
		if (self.runtime.mail_account.user != user) and not is_system_manager(user):
			frappe.throw(
				_("Mail Account {0} does not belong to user {1}.").format(
					frappe.bold(self.sender), frappe.bold(user)
				)
			)

		if not self.runtime.mail_account.enabled:
			frappe.throw(_("Mail Account {0} is disabled.").format(frappe.bold(self.sender)))

	def set_display_name(self) -> None:
		"""Sets the Display Name."""

		if not self.display_name:
			self.display_name = self.runtime.mail_account.display_name

	def set_reply_to(self) -> None:
		"""Sets the Reply To."""

		if not self.reply_to:
			self.reply_to = self.runtime.mail_account.reply_to

	def validate_in_reply_to(self) -> None:
		"""Validates the In Reply To."""

		if not self.in_reply_to_mail_type and not self.in_reply_to_mail_name:
			return

		if not self.in_reply_to_mail_type:
			frappe.throw(_("In Reply To Mail Type is required."))
		elif not self.in_reply_to_mail_name:
			frappe.throw(_("In Reply To Mail Name is required."))
		elif self.in_reply_to_mail_type not in ["Incoming Mail", "Outgoing Mail"]:
			frappe.throw(
				_("{0} must be either Incoming Mail or Outgoing Mail.").format(
					frappe.bold("In Reply To Mail Type")
				)
			)

		self.in_reply_to = get_in_reply_to(self.in_reply_to_mail_type, self.in_reply_to_mail_name)
		if not self.in_reply_to:
			frappe.throw(
				_("In Reply To Mail {0} - {1} does not exist.").format(
					frappe.bold(self.in_reply_to_mail_type), frappe.bold(self.in_reply_to_mail_name)
				)
			)

	def validate_recipients(self) -> None:
		"""Validates the recipients."""

		if not self.recipients:
			if self.get("_action") == "submit":
				frappe.throw(
					_("Please add at least one recipient before sending the mail."), frappe.MandatoryError
				)

			return

		max_recipients = self.runtime.mail_settings.max_recipients
		if len(self.recipients) > max_recipients:
			frappe.throw(
				_("Recipient limit exceeded ({0}). Maximum {1} recipient(s) allowed.").format(
					frappe.bold(len(self.recipients)), frappe.bold(max_recipients)
				)
			)

		recipients = []
		for recipient in self.recipients:
			recipient.email = recipient.email.strip().lower()

			if validate_email_address(recipient.email) != recipient.email:
				frappe.throw(
					_("Row #{0}: Invalid recipient {1}.").format(recipient.idx, frappe.bold(recipient.email))
				)

			type_email = (recipient.type, recipient.email)

			if type_email in recipients:
				frappe.throw(
					_("Row #{0}: Duplicate recipient {1} of type {2}.").format(
						recipient.idx, frappe.bold(recipient.email), frappe.bold(recipient.type)
					)
				)

			recipients.append(type_email)

	def validate_custom_headers(self) -> None:
		"""Validates the custom headers."""

		if not self.custom_headers:
			return

		max_headers = self.runtime.mail_settings.max_headers
		if len(self.custom_headers) > max_headers:
			frappe.throw(
				_("Custom Headers limit exceeded ({0}). Maximum {1} custom header(s) allowed.").format(
					frappe.bold(len(self.custom_headers)), frappe.bold(max_headers)
				)
			)

		custom_headers = []
		for header in self.custom_headers:
			if not header.key.upper().startswith("X-"):
				header.key = f"X-{header.key}"

			if header.key.upper().startswith("X-FM-"):
				frappe.throw(_("Custom header {0} is not allowed.").format(frappe.bold(header.key)))

			if header.key in custom_headers:
				frappe.throw(
					_("Row #{0}: Duplicate custom header {1}.").format(header.idx, frappe.bold(header.key))
				)
			else:
				custom_headers.append(header.key)

	def load_attachments(self) -> None:
		"""Loads the attachments."""

		FILE = frappe.qb.DocType("File")
		self.attachments = (
			frappe.qb.from_(FILE)
			.select(FILE.name, FILE.file_name, FILE.file_url, FILE.is_private, FILE.file_size)
			.where((FILE.attached_to_doctype == self.doctype) & (FILE.attached_to_name == self.name))
		).run(as_dict=True)

		for attachment in self.attachments:
			attachment.type = "attachment"

	def validate_attachments(self) -> None:
		"""Validates the attachments."""

		if not self.attachments:
			return

		max_attachments = self.runtime.mail_settings.max_attachments
		max_attachment_size = self.runtime.mail_settings.max_attachment_size_mb
		max_attachments_size = self.runtime.mail_settings.max_total_attachments_size_mb

		if len(self.attachments) > max_attachments:
			frappe.throw(
				_("Attachment limit exceeded ({0}). Maximum {1} attachment(s) allowed.").format(
					frappe.bold(len(self.attachments)),
					frappe.bold(max_attachments),
				)
			)

		total_attachments_size = 0
		for attachment in self.attachments:
			file_size = flt(attachment.file_size / 1024 / 1024, 3)
			if file_size > max_attachment_size:
				frappe.throw(
					_("Attachment size limit exceeded ({0} MB). Maximum {1} MB allowed.").format(
						frappe.bold(file_size), frappe.bold(max_attachment_size)
					)
				)

			total_attachments_size += file_size

		if total_attachments_size > max_attachments_size:
			frappe.throw(
				_("Attachments size limit exceeded ({0} MB). Maximum {1} MB allowed.").format(
					frappe.bold(total_attachments_size),
					frappe.bold(max_attachments_size),
				)
			)

	def validate_include_agent_groups(self) -> None:
		"""Validate include agent groups and set it to the value from the domain."""

		self.include_agent_groups = self.include_agent_groups or self.runtime.mail_domain.include_agent_groups

	def validate_exclude_agent_groups(self) -> None:
		"""Validate exclude agent groups and set it to the value from the domain."""

		self.exclude_agent_groups = self.exclude_agent_groups or self.runtime.mail_domain.exclude_agent_groups

	def validate_include_agents(self) -> None:
		"""Validate include agents and set it to the value from the domain."""

		self.include_agents = self.include_agents or self.runtime.mail_domain.include_agents

	def validate_exclude_agents(self) -> None:
		"""Validate exclude agents and set it to the value from the domain."""

		self.exclude_agents = self.exclude_agents or self.runtime.mail_domain.exclude_agents

	def set_ip_address(self) -> None:
		"""Sets the IP Address."""

		self.ip_address = frappe.local.request_ip

	def set_message_id(self) -> None:
		"""Sets the Message ID."""

		self.message_id = make_msgid(domain=self.domain_name)

	def set_body_html(self) -> None:
		"""Sets the HTML Body."""

		self.body_html = self.body_html or ""

		if self.via_api:
			self._correct_attachments_file_url()

	def set_body_plain(self) -> None:
		"""Sets the Plain Body."""

		self.body_plain = convert_html_to_text(self.body_html)

	def generate_message(self) -> None:
		"""Sets the Message."""

		def _get_message() -> MIMEMultipart | Message:
			"""Returns the MIME message."""

			if self.raw_message:
				parser = EmailParser(self.raw_message)

				if parser.get_date() > now():
					frappe.throw(_("Future date is not allowed."))

				if self.via_api:
					if self.runtime.mail_account.override_display_name_api:
						self.display_name = self.runtime.mail_account.display_name
					if self.runtime.mail_account.override_reply_to_api:
						if self.runtime.mail_account.reply_to:
							parser.update_header("Reply-To", self.runtime.mail_account.reply_to)
						else:
							del parser["Reply-To"]

				self.body_html = self.body_plain = None
				parser.update_header("From", formataddr((self.display_name, self.from_)))
				self.subject = parser.get_subject()
				self.reply_to = parser.get_reply_to()
				self.message_id = parser.get_message_id() or self.message_id
				self.in_reply_to = parser.get_in_reply_to()
				self.in_reply_to_mail_type, self.in_reply_to_mail_name = get_in_reply_to_mail(
					self.in_reply_to
				)
				parser.save_attachments(self.doctype, self.name, is_private=True)
				self.body_html, self.body_plain = parser.get_body()

				return parser.message

			message = MIMEMultipart("alternative", policy=policy.SMTP)

			if self.reply_to:
				message["Reply-To"] = self.reply_to

			if self.in_reply_to:
				message["In-Reply-To"] = self.in_reply_to

			message["From"] = formataddr((self.display_name, self.from_))

			for type in ["To", "Cc"]:
				if recipients := self._get_recipients(type):
					message[type] = recipients

			message["Subject"] = self.subject
			message["Date"] = formatdate(localtime=True)
			message["Message-ID"] = self.message_id

			body_html = self._replace_image_url_with_content_id()
			body_plain = convert_html_to_text(body_html)

			if self.runtime.mail_account.track_outgoing_mail:
				self.tracking_id = uuid7().hex
				body_html = add_tracking_pixel(body_html, self.tracking_id)

			message.attach(MIMEText(body_plain, "plain", "utf-8", policy=policy.SMTP))
			message.attach(MIMEText(body_html, "html", "utf-8", policy=policy.SMTP))

			return message

		def _add_headers(message: MIMEMultipart | Message) -> None:
			"""Adds the headers to the message."""

			received_header_value = f"from {get_host_by_ip(self.ip_address) or 'unknown-host'} ({self.ip_address}) by {frappe.local.site} (Frappe Mail) via HTTP; {formatdate()}"
			received_header = ("Received", received_header_value)
			message._headers.insert(0, received_header)

			if self.custom_headers:
				for header in self.custom_headers:
					message.add_header(header.key, header.value)

			del message["X-Priority"]
			message["X-Priority"] = str(self.priority)

			if self.is_newsletter:
				del message["X-Newsletter"]
				message["X-Newsletter"] = "1"

		def _add_attachments(message: MIMEMultipart | Message) -> None:
			"""Adds the attachments to the message."""

			for attachment in self.attachments:
				file = frappe.get_doc("File", attachment.get("name"))
				content_type = guess_type(file.file_name)[0]

				if content_type is None:
					content_type = "application/octet-stream"

				content = file.get_content()
				maintype, subtype = content_type.split("/", 1)

				if maintype == "text":
					if isinstance(content, str):
						content = content.encode("utf-8")
					part = MIMEText(content, _subtype=subtype, _charset="utf-8", policy=policy.SMTP)

				elif maintype == "image":
					part = MIMEImage(content, _subtype=subtype, policy=policy.SMTP)

				elif maintype == "audio":
					part = MIMEAudio(content, _subtype=subtype, policy=policy.SMTP)

				else:
					part = MIMEBase(maintype, subtype, policy=policy.SMTP)
					part.set_payload(content)
					encode_base64(part)

				part.add_header("Content-Disposition", f'{attachment.type}; filename="{file.file_name}"')
				part.add_header("Content-ID", f"<{attachment.name}>")

				message.attach(part)

		message = _get_message()
		_add_headers(message)
		_add_attachments(message)

		self.message = message.as_string()
		self.message_size = len(self.message)
		self.created_at = get_datetime_str(parsedate_to_datetime(message["Date"]))
		self.submitted_at = now()
		self.submitted_after = time_diff_in_seconds(self.submitted_at, self.created_at)

	def validate_max_message_size(self) -> None:
		"""Validates the maximum message size."""

		message_size = flt(self.message_size / 1024 / 1024, 3)
		max_message_size = self.runtime.mail_settings.max_message_size_mb

		if message_size > max_message_size:
			frappe.throw(
				_("Message size limit exceeded ({0} MB). Maximum {1} MB allowed.").format(
					frappe.bold(message_size), frappe.bold(max_message_size)
				)
			)

	def create_mail_contacts(self) -> None:
		"""Creates the mail contacts."""

		if self.runtime.mail_account.create_mail_contact:
			for rcpt in self.recipients:
				create_mail_contact(self.runtime.mail_account.user, rcpt.email, rcpt.display_name)

	def _add_recipient(self, type: str, recipient: str | list[str] | None = None) -> None:
		"""Adds the recipients."""

		if not recipient:
			return

		recipients = [recipient] if isinstance(recipient, str) else recipient
		for rcpt in recipients:
			display_name, email = parseaddr(rcpt)

			if not email:
				frappe.throw(_("Invalid format for recipient {0}.").format(frappe.bold(rcpt)))

			self.append("recipients", {"type": type, "email": email, "display_name": display_name})

	def _get_recipients(self, type: str | None = None, as_list: bool = False) -> str | list[str]:
		"""Returns the recipients."""

		recipients = []
		for rcpt in self.recipients:
			if type and rcpt.type != type:
				continue

			recipients.append(formataddr((rcpt.display_name, rcpt.email)))

		return recipients if as_list else ", ".join(recipients)

	def _update_recipients(self, type: str, recipients: list[str] | None = None) -> None:
		"""Updates the recipients by comparing new and old list."""

		prev_recipients = self._get_recipients(type, as_list=True)
		for rcpt in recipients:
			if rcpt not in prev_recipients:
				self._add_recipient(type, rcpt)

		for rcpt in self.recipients[:]:
			if rcpt.type == type and rcpt.email not in recipients:
				self.recipients.remove(rcpt)

	def _add_attachment(self, attachment: dict | list[dict]) -> None:
		"""Adds the attachments."""

		if not attachment:
			return

		attachments = [attachment] if isinstance(attachment, dict) else attachment
		for a in attachments:
			filename = a.get("filename")
			content = a["content"]

			kwargs = {
				"dt": self.doctype,
				"dn": self.name,
				"df": "file",
				"fname": filename,
				"content": content,
				"is_private": 1,
				"decode": True,
			}
			file = save_file(**kwargs)

			if filename and filename != file.file_name:
				file.db_set("file_name", filename, update_modified=False)

	def _add_custom_headers(self, headers: dict) -> None:
		"""Adds the custom headers."""

		if headers and isinstance(headers, dict):
			for key, value in headers.items():
				self.append("custom_headers", {"key": key, "value": value})

	def _replace_image_url_with_content_id(self) -> str:
		"""Replaces the image URL with content ID."""

		body_html = self.body_html or ""

		if body_html and self.attachments:
			img_src_pattern = r'<img.*?src=[\'"](.*?)[\'"].*?>'

			for img_src_match in finditer(img_src_pattern, body_html):
				img_src = img_src_match.group(1)

				if content_id := self._get_attachment_content_id(img_src, set_as_inline=True):
					body_html = body_html.replace(img_src, f"cid:{content_id}")

		return body_html

	def _get_attachment_content_id(self, file_url: str, set_as_inline: bool = False) -> str | None:
		"""Returns the attachment content ID."""

		if not file_url:
			return

		field = "file_url"
		parsed_url = urlparse(file_url)
		value = parsed_url.path

		if query_params := parse_qs(parsed_url.query):
			if fid := query_params.get("fid", [None])[0]:
				field = "name"
				value = fid

		for attachment in self.attachments:
			if attachment[field] == value:
				if set_as_inline:
					attachment.type = "inline"

				return attachment.name

	def _correct_attachments_file_url(self) -> None:
		"""Corrects the attachments file URL."""

		if self.body_html and self.attachments:
			img_src_pattern = r'<img.*?src=[\'"](.*?)[\'"].*?>'

			for img_src_match in finditer(img_src_pattern, self.body_html):
				img_src = img_src_match.group(1)

				if file_url := self._get_attachment_file_url(img_src):
					self.body_html = self.body_html.replace(img_src, file_url)

	def _get_attachment_file_url(self, src: str) -> str | None:
		"""Returns the attachment file URL."""

		for attachment in self.attachments:
			if src == attachment.file_name:
				return attachment.file_url

	def _sync_with_frontend(self, status: str) -> None:
		"""Triggered to sync the document with the frontend."""

		if self.via_api and status == "Sent":
			frappe.publish_realtime("outgoing_mail_sent", self.as_dict(), after_commit=True)

	def _db_set(
		self,
		update_modified: bool = True,
		commit: bool = False,
		notify_update: bool = False,
		**kwargs,
	) -> None:
		"""Updates the document with the given key-value pairs."""

		self.db_set(kwargs, update_modified=update_modified, commit=commit)

		if notify_update:
			self.notify_update()

	def update_status(
		self, status: str | None = None, db_set: bool = False, notify_update: bool = False
	) -> None:
		"""Updates the status of the email based on the status of the recipients."""

		if not status:
			recipient_statuses = [r.status for r in self.recipients]
			total_statuses = len(recipient_statuses)
			status_counts = {
				k: recipient_statuses.count(k) for k in ["", "Blocked", "Deferred", "Bounced", "Sent"]
			}

			if status_counts[""] == total_statuses:  # All recipients are in pending state (no status)
				return

			if status_counts["Blocked"] == total_statuses:  # All recipients are blocked
				status = "Blocked"
			elif status_counts["Deferred"] > 0:  # Any recipient is deferred
				status = "Deferred"
			elif status_counts["Sent"] == total_statuses:  # All recipients are sent
				status = "Sent"
			elif status_counts["Sent"] > 0:  # Any recipient is sent
				status = "Partially Sent"
			elif (
				status_counts["Bounced"] > 0
			):  # All recipients are bounced or some are blocked and some are bounced
				status = "Bounced"

		if status:
			self.status = status

			if db_set:
				self._db_set(status=status, notify_update=notify_update)

	def enqueue_process_for_delivery(self) -> None:
		"""Enqueue the job to process the email for delivery."""

		# Emails with priority 1 are considered high-priority and should be enqueued at the front.
		# Note: Existing jobs with priority 1 in the queue may lead to concurrent processing,
		# which is acceptable (for now) as multiple workers can handle jobs in parallel.
		at_front = self.priority == 1

		frappe.enqueue_doc(
			self.doctype,
			self.name,
			"process_for_delivery",
			queue="short",
			enqueue_after_commit=True,
			at_front=at_front,
		)

	def process_for_delivery(self) -> None:
		"""Process the email for delivery."""

		# Reload the doc to ensure it reflects the latest status.
		# This handles cases where the email's status might have been manually updated (e.g., Accepted) after the job was created.
		self.reload()
		if self.status != "Pending":
			return

		kwargs = self._prepare_delivery_args()
		self._db_set(notify_update=True, **kwargs)

		if self.status == "Blocked":
			self._sync_with_frontend(self.status)
		elif self.status == "Accepted":
			frappe.flags.force_transfer = True
			self.transfer_to_mail_agent()

	def _prepare_delivery_args(self) -> dict:
		"""Prepare arguments for delivery processing."""

		kwargs = {"status": "Accepted"}

		for rcpt in self.recipients:
			if is_email_blocked(rcpt.email):
				rcpt.status = "Blocked"
				rcpt.error_message = _(
					"Delivery to this recipient was blocked because their email address is on our blocklist. This action was taken after repeated delivery failures to this address. To protect your sender reputation and prevent further issues, this email was not sent to the blocked recipient."
				)
				rcpt.db_update()

		self.update_status()
		if self.status == "Blocked":
			kwargs.update(
				{
					"status": "Blocked",
					"error_message": _(
						"Delivery of this email was blocked because all recipients are on our blocklist. Repeated delivery failures to these addresses have led to their blocking. To protect your sender reputation and avoid further issues, this email was not sent. Please review the recipient list or contact support for assistance."
					),
				}
			)

		if kwargs["status"] == "Accepted" and is_spam_detection_enabled_for_outbound():
			kwargs.update(self._check_for_spam())

		kwargs["processed_at"] = now()
		kwargs["processed_after"] = time_diff_in_seconds(kwargs["processed_at"], self.submitted_at)

		return kwargs

	def _check_for_spam(self) -> dict:
		"""Check the message for spam and update the status if necessary."""

		log = create_spam_check_log(self.message)
		mail_settings = frappe.get_cached_doc("Mail Settings")
		is_spam = log.spam_score > mail_settings.spamd_outbound_threshold
		short_error_message = None
		kwargs = {
			"spam_score": log.spam_score,
			"spam_check_log": log.name,
			"is_spam": cint(is_spam),
		}

		if is_spam and mail_settings.spamd_outbound_block:
			short_error_message = _("Spam score exceeded the permitted threshold.")
			kwargs.update(
				{
					"status": "Blocked",
					"error_message": _(
						"This email has been blocked because our system flagged it as spam. The spam score exceeded the permitted threshold. To resolve this, review your email content, remove any potentially suspicious links or attachments, and try sending it again. If the issue persists, please contact our support team for assistance."
					),
				}
			)

		if kwargs.get("status") == "Blocked":
			for rcpt in self.recipients:
				rcpt.status = "Blocked"
				rcpt.error_message = short_error_message
				rcpt.db_update()

		return kwargs

	def _accept(self) -> None:
		"""Accept the email and set status to `Accepted`."""

		processed_at = now()
		processed_after = time_diff_in_seconds(processed_at, self.submitted_at)
		self._db_set(
			status="Accepted",
			error_message=None,
			processed_at=processed_at,
			processed_after=processed_after,
			notify_update=True,
		)

	@frappe.whitelist()
	def force_accept(self) -> None:
		"""Forces accept the email."""

		frappe.only_for("System Manager")

		if self.status in ["Pending", "Blocked"]:
			for rcpt in self.recipients:
				if rcpt.status == "Blocked":
					rcpt.status = ""
					rcpt.error_message = None
					rcpt.db_update()

			self._accept()
			self.add_comment(
				"Comment", _("Mail accepted by System Manager {0}.").format(frappe.bold(frappe.session.user))
			)

			if self.priority == 1:
				frappe.flags.force_transfer = True
				self.transfer_to_mail_agent()

	@frappe.whitelist()
	def retry_failed(self) -> None:
		"""Retries the failed mail."""

		if self.docstatus == 1 and self.status == "Failed" and self.failed_count < MAX_FAILED_COUNT:
			self._db_set(status="Accepted", error_log=None, error_message=None, commit=True)
			self.transfer_to_mail_agent()

	@frappe.whitelist()
	def force_transfer_to_mail_agent(self) -> None:
		"""Forces transfer the email to the agent for sending."""

		frappe.only_for("System Manager")
		if self.status in ["Transferring"]:
			frappe.flags.force_transfer = True
			self.transfer_to_mail_agent()

	@frappe.whitelist()
	def retry_bounced(self) -> None:
		"""Retries bounced email."""

		frappe.only_for("System Manager")
		if self.status == "Bounced":
			self._db_set(status="Accepted", error_log=None, error_message=None, commit=True)
			self.transfer_to_mail_agent()

	@frappe.whitelist()
	def transfer_to_mail_agent(self) -> None:
		"""Transfers the email to the Mail Agent."""

		if not frappe.flags.force_transfer:
			self.reload()

			# Ensure the document is submitted and has "Accepted" status
			if not (
				self.docstatus == 1 and self.status in ["Accepted"] and self.failed_count < MAX_FAILED_COUNT
			):
				return

		transfer_started_at = now()
		self._db_set(
			status="Transferring",
			transfer_started_at=transfer_started_at,
			transfer_started_after=time_diff_in_seconds(transfer_started_at, self.processed_at),
			notify_update=False,
			commit=True,
		)

		try:
			# Remove duplicate recipients while preserving the order by using `dict.fromkeys()`.
			# This avoids using a set, which could change the order of recipients.
			recipients = list(
				dict.fromkeys(
					[rcpt.email for rcpt in self.recipients if rcpt.status not in ["Blocked", "Sent"]]
				)
			)

			if not recipients:
				frappe.throw(_("All recipients are blocked or sent."))

			agent_or_group = get_random_agent_or_agent_group(
				self.include_agent_groups, self.exclude_agent_groups, self.include_agents, self.exclude_agents
			)

			mail_account = frappe.get_cached_doc("Mail Account", self.sender)
			username = mail_account.email
			password = mail_account.get_password("password")

			with SMTPContext(agent_or_group, 465, username, password, use_ssl=True) as server:
				mail_options = [f"ENVID={self.name}:{self.token}", f"MT-PRIORITY={self.priority}"]
				server.sendmail(self.from_, recipients, self.message, mail_options=mail_options)

			transfer_completed_at = now()
			transfer_completed_after = time_diff_in_seconds(transfer_completed_at, transfer_started_at)

			for rcpt in self.recipients:
				if rcpt.email in recipients:
					rcpt.status = "Sent"
					rcpt.db_update()

			self.update_status()
			self._db_set(
				status=self.status,
				transfer_completed_at=transfer_completed_at,
				transfer_completed_after=transfer_completed_after,
				notify_update=True,
				commit=True,
			)
		except Exception:
			error_log = frappe.get_traceback(with_context=False)
			failed_count = self.failed_count + 1
			self._db_set(
				status="Failed",
				error_log=error_log,
				failed_count=failed_count,
				retry_after=get_retry_after(failed_count),
				notify_update=True,
				commit=True,
			)


@frappe.whitelist()
def get_from_() -> str | None:
	"""Returns the default outgoing email address of the user."""

	return get_default_outgoing_email_for_user(frappe.session.user)


@frappe.whitelist()
def reply_to_mail(source_name, target_doc=None) -> "OutgoingMail":
	"""Creates an Outgoing Mail as a reply to the given Outgoing Mail."""

	in_reply_to_mail_type = "Outgoing Mail"
	source_doc = frappe.get_doc(in_reply_to_mail_type, source_name)
	target_doc = target_doc or frappe.new_doc("Outgoing Mail")

	target_doc.in_reply_to_mail_type = source_doc.doctype
	target_doc.in_reply_to_mail_name = source_name
	target_doc.from_ = source_doc.from_
	target_doc.subject = f"Re: {source_doc.subject}"

	recipient_types = ["To", "Cc"] if frappe.flags.args.all else ["To"]
	for recipient in source_doc.recipients:
		if recipient.type in recipient_types:
			target_doc.append(
				"recipients",
				{
					"type": recipient.type,
					"email": recipient.email,
					"display_name": recipient.display_name,
				},
			)

	return target_doc


def add_tracking_pixel(body_html: str, tracking_id: str) -> str:
	"""Adds the tracking pixel to the HTML body."""

	src = f"{frappe.utils.get_url()}/api/method/mail.api.track.open?id={tracking_id}"
	tracking_pixel = f'<img src="{src}">'

	if "<body>" in body_html:
		body_html = body_html.replace("<body>", f"<body>{tracking_pixel}", 1)
	else:
		body_html = f"<html><body>{tracking_pixel}{body_html}</body></html>"

	return body_html


def is_spam_detection_enabled_for_outbound() -> bool:
	"""Returns True if spam detection is enabled for outbound emails else False."""

	mail_settings = frappe.get_cached_doc("Mail Settings")
	return mail_settings.enable_spamd and mail_settings.enable_spamd_for_outbound


def get_retry_after(failed_count: int) -> str:
	"""Returns the retry after datetime."""

	retry_after_minutes = failed_count * (failed_count + 1)  # 2, 6, 12, 20, 30 ...
	return add_to_date(now(), minutes=retry_after_minutes)


def get_random_agent_or_agent_group(
	include_agent_groups: str | list[str] | None = None,
	exclude_agent_groups: str | list[str] | None = None,
	include_agents: str | list[str] | None = None,
	exclude_agents: str | list[str] | None = None,
	raise_if_not_found: bool = True,
) -> str:
	"""Returns a random agent or agent group based on the given criteria."""

	def normalize_input(value: str | list[str] | None) -> list[str]:
		"""Normalize input to a list of strings."""

		if isinstance(value, str):
			return value.split("\n")
		return value or []

	include_agent_groups = normalize_input(include_agent_groups)
	exclude_agent_groups = normalize_input(exclude_agent_groups)
	include_agents = normalize_input(include_agents)
	exclude_agents = normalize_input(exclude_agents)

	selected_agent = None
	selected_agent_group = None
	agent_groups = set(frappe.db.get_all("Mail Agent Group", {"enabled": 1, "outbound": 1}, pluck="name"))

	if include_agents or exclude_agents:
		agents = set(frappe.db.get_all("Mail Agent", {"enabled": 1, "enable_outbound": 1}, pluck="name"))
		if include_agents:
			if invalid_agents := [agent for agent in include_agents if agent and agent not in agents]:
				frappe.throw(
					_("The following agents do not exist or are not enabled for outbound: {0}").format(
						", ".join(invalid_agents)
					)
				)
				agents.intersection_update(include_agents)

		if exclude_agents:
			agents.difference_update(exclude_agents)

		selected_agent = random.choice(list(agents))
	else:
		if include_agent_groups:
			if invalid_groups := [
				group for group in include_agent_groups if group and group not in agent_groups
			]:
				frappe.throw(
					_("The following agent groups do not exist or are not enabled for outbound: {0}").format(
						", ".join(invalid_groups)
					)
				)
				agent_groups.intersection_update(include_agent_groups)

		if exclude_agent_groups:
			agent_groups.difference_update(exclude_agent_groups)

		selected_agent_group = random.choice(list(agent_groups))

	if not selected_agent and not selected_agent_group and raise_if_not_found:
		frappe.throw(_("No agent or agent group found based on the given criteria."))

	return selected_agent or selected_agent_group


def create_outgoing_mail(
	from_: str,
	to: str | list[str],
	display_name: str | None = None,
	cc: str | list[str] | None = None,
	bcc: str | list[str] | None = None,
	subject: str | None = None,
	body_html: str | None = None,
	reply_to: str | list[str] | None = None,
	in_reply_to_mail_type: str | None = None,
	in_reply_to_mail_name: str | None = None,
	custom_headers: dict | None = None,
	attachments: list[dict] | None = None,
	raw_message: str | None = None,
	via_api: int = 0,
	is_newsletter: int = 0,
	do_not_save: bool = False,
	do_not_submit: bool = False,
) -> "OutgoingMail":
	"""Creates the outgoing mail."""

	doc: OutgoingMail = frappe.new_doc("Outgoing Mail")
	doc.from_ = from_
	doc.display_name = display_name
	doc._add_recipient("To", to)
	doc._add_recipient("Cc", cc)
	doc._add_recipient("Bcc", bcc)
	doc.subject = subject
	doc.body_html = body_html
	doc.reply_to = reply_to
	doc.in_reply_to_mail_type = in_reply_to_mail_type
	doc.in_reply_to_mail_name = in_reply_to_mail_name
	doc._add_custom_headers(custom_headers)
	doc.raw_message = raw_message
	doc.via_api = via_api
	doc.is_newsletter = is_newsletter

	if via_api and not is_newsletter:
		user = frappe.session.user
		if from_ not in get_user_email_addresses(user):
			from_ = get_default_outgoing_email_for_user(user)

	if not do_not_save:
		doc.save()
		doc._add_attachment(attachments)
		if not do_not_submit:
			doc.submit()

	return doc


def transfer_emails_to_agent() -> None:
	"""Transfers the emails to the agent for sending."""

	OM = frappe.qb.DocType("Outgoing Mail")
	mails = (
		frappe.qb.from_(OM)
		.select(OM.name)
		.where(
			(OM.docstatus == 1)
			& (
				(OM.status == "Pending")
				| ((OM.status == "Failed") & (Now() >= OM.retry_after))
				| ((OM.status == "Transferring") & (OM.transfer_started_at <= (Now() - Interval(minutes=10))))
			)
		)
		.orderby(OM.priority, order=Order.desc)
		.orderby(OM.failed_count, OM.submitted_at, order=Order.asc)
		.limit(500)
	).run(pluck="name")

	if not mails:
		return

	failed_mails = []
	for mail in mails:
		try:
			outgoing_mail: OutgoingMail = frappe.get_doc("Outgoing Mail", mail)
			if outgoing_mail.status == "Pending":
				outgoing_mail.process_for_delivery()
			elif outgoing_mail.status == "Failed":
				outgoing_mail.retry_failed()
			elif outgoing_mail.status == "Transferring":
				outgoing_mail.force_transfer_to_mail_agent()
		except Exception:
			failed_mails.append(mail.name)
			failed_count = len(failed_mails)
			total_count = len(mails)
			failure_rate = failed_count / total_count
			if (failure_rate > 0.33) and (failed_count > 50):
				frappe.throw(
					_(
						"Too many email transfer failures: {failed_count}/{total_count} ({failure_rate:.2%}). Process halted to prevent further issues."
					).format(failed_count=failed_count, total_count=total_count, failure_rate=failure_rate)
				)


def delete_newsletters() -> None:
	"""Called by the scheduler to delete the newsletters based on the retention."""

	newsletter_retention_and_mail_domains_map = {}
	for mail_domain in frappe.db.get_list(
		"Mail Domain",
		fields=["name", "newsletter_retention"],
		order_by="newsletter_retention",
	):
		newsletter_retention_and_mail_domains_map.setdefault(mail_domain["newsletter_retention"], []).append(
			mail_domain["name"]
		)

	for retention_days, mail_domains in newsletter_retention_and_mail_domains_map.items():
		OM = frappe.qb.DocType("Outgoing Mail")
		(
			frappe.qb.from_(OM)
			.where(
				(OM.docstatus != 0)
				& (OM.status == "Sent")
				& (OM.is_newsletter == 1)
				& (OM.domain_name.isin(mail_domains))
				& (OM.submitted_at < (Now() - Interval(days=retention_days)))
			)
			.delete()
		).run()


def has_permission(doc: "Document", ptype: str, user: str | None = None) -> bool:
	if doc.doctype != "Outgoing Mail":
		return False

	user = user or frappe.session.user
	user_is_system_manager = is_system_manager(user)
	user_is_account_owner = is_account_owner(doc.sender, user)

	if ptype == "create":
		return True
	elif ptype in ["write", "cancel"]:
		return user_is_system_manager or user_is_account_owner
	else:
		return user_is_system_manager or (user_is_account_owner and doc.docstatus != 2)


def get_permission_query_condition(user: str | None = None) -> str:
	user = user or frappe.session.user

	if is_system_manager(user):
		return ""

	if account := get_account_for_user(user):
		return f"(`tabOutgoing Mail`.`sender` = {frappe.db.escape(account)}) AND (`tabOutgoing Mail`.`docstatus` != 2)"
	else:
		return "1=0"
