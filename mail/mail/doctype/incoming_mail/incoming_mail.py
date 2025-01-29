# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
import time
from email.utils import parseaddr
from typing import TYPE_CHECKING, Literal

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, time_diff_in_seconds
from uuid_utils import uuid7

from mail.imap import IMAPContext
from mail.mail.doctype.bounce_log.bounce_log import create_or_update_bounce_log
from mail.mail.doctype.dmarc_report.dmarc_report import create_dmarc_report
from mail.mail.doctype.mail_contact.mail_contact import create_mail_contact
from mail.mail.doctype.mime_message.mime_message import (
	create_mime_message,
	get_mime_message,
	update_mime_message,
)
from mail.utils import get_dmarc_address, get_in_reply_to_mail, load_compressed_file
from mail.utils.cache import get_account_for_user
from mail.utils.email_parser import EmailParser, extract_ip_and_host, extract_spam_status
from mail.utils.user import is_mail_account_owner, is_system_manager

if TYPE_CHECKING:
	from mail.mail.doctype.outgoing_mail.outgoing_mail import OutgoingMail


class IncomingMail(Document):
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
		self.validate_fetched_at()
		self.validate_mandatory_fields()
		if self.get("_action") == "submit":
			self.process()

	def on_submit(self) -> None:
		self.create_mail_contact()
		self.sync_with_frontend()

	def on_cancel(self) -> None:
		self.status = "Cancelled"

	def on_trash(self) -> None:
		if frappe.session.user != "Administrator":
			frappe.throw(_("Only Administrator can delete Incoming Mail."))

	def validate_fetched_at(self) -> None:
		"""Set `fetched_at` to current datetime if not set."""

		if not self.fetched_at:
			self.fetched_at = now()

	def validate_mandatory_fields(self) -> None:
		"""Validates the mandatory fields."""

		mandatory_fields = ["receiver", "_message"]
		for field in mandatory_fields:
			if not self.get(field):
				field_label = frappe.get_meta(self.doctype).get_label(field)
				frappe.throw(_("{0} is mandatory.").format(field_label))

	def process(self) -> None:
		"""Processes the Incoming Mail."""

		self.status = "Submitted"

		parser = EmailParser(self.message)
		self.display_name, self.sender = parser.get_sender()
		self.domain_name = self.receiver.split("@")[1]
		self.subject = parser.get_subject()
		self.reply_to = parser.get_reply_to()
		self.message_id = parser.get_message_id()
		self.created_at = parser.get_date()
		self.message_size = parser.get_size()
		self.from_ip, self.from_host = extract_ip_and_host(parser.get_header("Received"))
		self.is_spam, self.spam_score = extract_spam_status(parser.get_header("X-Spam-Status"))
		self.in_reply_to = parser.get_in_reply_to()
		self.in_reply_to_mail_type, self.in_reply_to_mail_name = get_in_reply_to_mail(self.in_reply_to)

		parser.save_attachments(self.doctype, self.name, is_private=True)
		self.body_html, self.body_plain = parser.get_body()

		for recipient in parser.get_recipients():
			self.append("recipients", recipient)

		for key, value in parser.get_authentication_results().items():
			setattr(self, key, value)

		if self.receiver == get_dmarc_address():
			self.create_dmarc_report()

		if (
			parser.message.get_content_type() == "multipart/report"
			and parser.message.get_param("report-type") == "delivery-status"
		):
			self.process_dsn_report(parser.message)

		if self.created_at:
			self.fetched_after = time_diff_in_seconds(self.fetched_at, self.created_at)

		self.processed_at = now()
		self.processed_after = time_diff_in_seconds(self.processed_at, self.fetched_at)

	def create_dmarc_report(self) -> None:
		"""Creates a DMARC Report from the Incoming Mail."""

		try:
			attachments = frappe.db.get_all(
				"File",
				filters={"attached_to_doctype": self.doctype, "attached_to_name": self.name},
				pluck="name",
			)
			for attachment in attachments:
				file = frappe.get_doc("File", attachment)
				xml_content = load_compressed_file(file_data=file.get_content())
				create_dmarc_report(xml_content, incoming_mail=self.name)

			self.type = "DMARC Report"
		except Exception:
			frappe.log_error(
				title=_("DMARC Report Creation Failed"),
				message=frappe.get_traceback(with_context=True),
			)

	def process_dsn_report(self, message) -> None:
		"""Processes the DSN Report."""

		try:
			original_envelope_id = None
			token = None

			for part in message.walk():
				if part.get("Original-Envelope-Id"):
					original_envelope_id, token = part.get("Original-Envelope-Id").split(":")
					break

			if not original_envelope_id or not token:
				frappe.throw(_("Original Envelope Id or Token not found in DSN Report."))

			outgoing_mail = frappe.get_doc("Outgoing Mail", original_envelope_id)
			if outgoing_mail.token != token:
				frappe.throw(_("Token mismatch in DSN Report."))

			dsn_data = []
			required_headers = [
				"Final-Recipient",
				"Action",
				"Status",
				"Diagnostic-Code",
				"Remote-MTA",
			]
			_rcpt_data = {}
			for part in message.walk():
				for header in required_headers:
					if part.get(header):
						_rcpt_data[header] = part.get(header)

				if len(_rcpt_data) == len(required_headers):
					dsn_data.append(_rcpt_data)
					_rcpt_data = {}

			rcpt_status_changed = False
			for rcpt_data in dsn_data:
				final_recipient = rcpt_data["Final-Recipient"].split("rfc822;")[1].strip()
				diagnostic_code = rcpt_data["Diagnostic-Code"].split("smtp;")[1].strip()
				remote_mta = rcpt_data["Remote-MTA"].split("dns;")[1].strip()
				response = json.dumps(
					{
						"status": rcpt_data["Status"],
						"diagnostic_code": diagnostic_code,
						"remote_mta": remote_mta,
					},
					indent=4,
				)

				for rcpt in outgoing_mail.recipients:
					if rcpt.email == final_recipient:
						rcpt_status_changed = True
						rcpt.status = "Bounced"
						rcpt.response = response
						rcpt.db_update()

						if rcpt.status == "Bounced":
							create_or_update_bounce_log(rcpt.email, bounce_increment=1)

			if rcpt_status_changed:
				outgoing_mail.update_status(db_set=True, notify_update=True)

			self.type = "DSN Report"

		except Exception:
			frappe.log_error(
				title=_("Process DSN Report Failed"),
				message=frappe.get_traceback(with_context=True),
			)

	def create_mail_contact(self) -> None:
		"""Creates the mail contact."""

		if frappe.get_cached_value("Mail Account", self.receiver, "create_mail_contact"):
			user = frappe.get_cached_value("Mail Account", self.receiver, "user")
			create_mail_contact(user, self.sender, self.display_name)

	def sync_with_frontend(self) -> None:
		"""Syncs the Incoming Mail with the frontend."""

		frappe.publish_realtime(
			"incoming_mail_received", self.as_dict(), user=self.receiver, after_commit=True
		)


@frappe.whitelist()
def reply_to_mail(source_name, target_doc=None) -> "OutgoingMail":
	"""Creates an Outgoing Mail as a reply to the Incoming Mail."""

	in_reply_to_mail_type = "Incoming Mail"
	source_doc = frappe.get_doc(in_reply_to_mail_type, source_name)
	target_doc = target_doc or frappe.new_doc("Outgoing Mail")

	target_doc.in_reply_to_mail_type = source_doc.doctype
	target_doc.in_reply_to_mail_name = source_name
	target_doc.subject = f"Re: {source_doc.subject}"

	email = source_doc.sender
	display_name = source_doc.display_name

	if source_doc.reply_to:
		display_name, email = parseaddr(source_doc.reply_to)

	target_doc.append(
		"recipients",
		{"type": "To", "email": email, "display_name": display_name},
	)

	if frappe.flags.args.all:
		recipients = [email, source_doc.receiver]
		for recipient in source_doc.recipients:
			if (recipient.type in ["To", "Cc"]) and (recipient.email not in recipients):
				recipients.append(recipient.email)
				target_doc.append(
					"recipients",
					{
						"type": "Cc",
						"email": recipient.email,
						"display_name": recipient.display_name,
					},
				)

	return target_doc


def has_permission(doc: "Document", ptype: str, user: str) -> bool:
	if doc.doctype != "Incoming Mail":
		return False

	user_is_system_manager = is_system_manager(user)
	user_is_account_owner = is_mail_account_owner(doc.receiver, user)

	if ptype in ["create", "submit"]:
		return user_is_system_manager
	elif ptype in ["write", "cancel"]:
		return user_is_system_manager or user_is_account_owner
	else:
		return user_is_system_manager or (user_is_account_owner and doc.docstatus == 1)


def get_permission_query_condition(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if is_system_manager(user):
		return ""

	if account := get_account_for_user(user):
		return f'(`tabIncoming Mail`.`receiver` = "{account}") AND (`tabIncoming Mail`.`docstatus` = 1)'
	else:
		return "1=0"


def create_incoming_mail(
	receiver: str,
	folder: Literal["Inbox", "Spam"],
	agent_group: str,
	message: str,
	do_not_save: bool = False,
	do_not_submit: bool = False,
) -> "IncomingMail":
	"""Creates an Incoming Mail."""

	doc = frappe.new_doc("Incoming Mail")
	doc.receiver = receiver
	doc.folder = folder
	doc.agent_group = agent_group
	doc.message = message

	if not do_not_save:
		doc.flags.ignore_links = True
		doc.insert(ignore_permissions=True)

		if not do_not_submit:
			try:
				doc.submit()
			except Exception:
				frappe.log_error(title=_("Submit Incoming Mail"), message=frappe.get_traceback())

	return doc


def fetch_emails_from_mail_agent(agent_group: str, accounts: list[str]) -> None:
	"""Called by scheduler to fetch emails from mail agent."""

	folders = ["Inbox", "Junk Mail"]

	for account in accounts:
		max_failures = 3
		total_failures = 0

		try:
			account = frappe.get_cached_doc("Mail Account", account)
			username = account.email
			password = account.get_password("password")

			with IMAPContext(agent_group, 993, username, password, use_ssl=True) as server:
				for folder in folders:
					_folder = "Spam" if folder == "Junk Mail" else folder
					while True:
						status, response = server.select(f'"{folder}"')
						if status != "OK":
							break

						status, message_numbers = server.search(None, "ALL")
						if status != "OK" or not message_numbers[0]:
							break

						for num in message_numbers[0].split():
							status, data = server.fetch(num, "(RFC822)")

							if status == "OK" and data:
								message = data[0][1].decode("utf-8")
								create_incoming_mail(account.name, _folder, agent_group, message)
								server.store(num, "+FLAGS", r"(\Deleted)")

						server.expunge()
		except Exception:
			total_failures += 1
			error_log = frappe.get_traceback(with_context=False)
			frappe.log_error(title=_(f"Fetch Emails {agent_group} : {account.email}"), message=error_log)

			if total_failures < max_failures:
				time.sleep(2**total_failures)


def fetch_emails_from_mail_agents(
	agent_groups: list[str] | None = None, accounts: list[str] | None = None
) -> None:
	"""Called by scheduler to fetch emails from mail agents."""

	agent_groups = agent_groups or frappe.db.get_all(
		"Mail Agent Group", {"enabled": 1, "inbound": 1}, pluck="name"
	)

	if not agent_groups:
		return

	accounts = accounts or frappe.db.get_all("Mail Account", {"enabled": 1}, pluck="name")
	if not accounts:
		return

	if frappe.flags.do_not_enqueue:
		for group in agent_groups:
			fetch_emails_from_mail_agent(group, accounts)
	else:
		for group in agent_groups:
			frappe.enqueue(
				fetch_emails_from_mail_agent,
				queue="long",
				job_name=f"Fetch Emails from {group}",
				agent_group=group,
				accounts=accounts,
			)
