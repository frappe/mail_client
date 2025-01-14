import re
from email.utils import parseaddr

import frappe
from bs4 import BeautifulSoup
from frappe.translate import get_all_translations
from frappe.utils import is_html

from mail.utils.cache import get_user_default_mail_account
from mail.utils.user import get_user_email_addresses, has_role, is_system_manager


def check_app_permission() -> bool:
	"""Returns True if the user has permission to access the app."""

	user = frappe.session.user
	return has_role(user, "Mail User") or is_system_manager(user)


@frappe.whitelist(allow_guest=True)
def get_branding() -> dict:
	"""Returns branding information."""

	return {
		"brand_name": frappe.db.get_single_value("Website Settings", "app_name"),
		"brand_html": frappe.db.get_single_value("Website Settings", "brand_html"),
		"favicon": frappe.db.get_single_value("Website Settings", "favicon"),
	}


@frappe.whitelist(allow_guest=True)
def get_user_info() -> dict:
	"""Returns user information."""

	if frappe.session.user == "Guest":
		return None

	user = frappe.db.get_value(
		"User",
		frappe.session.user,
		["name", "email", "enabled", "user_image", "full_name", "user_type", "username", "api_key"],
		as_dict=1,
	)
	user["roles"] = frappe.get_roles(user.name)
	user.mail_user = "Mail User" in user.roles

	return user


@frappe.whitelist(allow_guest=True)
def get_translations() -> dict:
	"""Returns translations for the current user's language."""

	if frappe.session.user != "Guest":
		language = frappe.db.get_value("User", frappe.session.user, "language")
	else:
		language = frappe.db.get_single_value("System Settings", "language")

	return get_all_translations(language)


@frappe.whitelist()
def get_incoming_mails(start: int = 0) -> list:
	"""Returns incoming mails for the current user."""

	mailboxes = get_user_email_addresses(frappe.session.user, "Incoming")

	mails = frappe.get_all(
		"Incoming Mail",
		{"receiver": ["in", mailboxes], "docstatus": 1},
		[
			"name",
			"sender",
			"body_html",
			"body_plain",
			"display_name",
			"subject",
			"creation",
			"in_reply_to_mail_name",
			"in_reply_to_mail_type",
			"message_id",
		],
		limit=50,
		start=start,
		order_by="created_at desc",
	)

	return get_mail_list(mails, "Incoming Mail")


@frappe.whitelist()
def get_sent_mails(start: int = 0) -> list:
	"""Returns sent mails for the current user."""

	return get_outgoing_mails("Sent", start)


@frappe.whitelist()
def get_draft_mails(start: int = 0) -> list:
	"""Returns draft mails for the current user."""

	return get_outgoing_mails("Draft", start)


def get_outgoing_mails(status: str, start: int = 0) -> list:
	"""Returns outgoing mails for the current user."""

	mailboxes = get_user_email_addresses(frappe.session.user, "Outgoing")

	if status == "Draft":
		docstatus = 0
		order_by = "modified desc"
	else:
		docstatus = 1
		# TODO: fix sorting
		order_by = "created_at desc"

	mails = frappe.get_all(
		"Outgoing Mail",
		{"sender": ["in", mailboxes], "docstatus": docstatus, "status": status},
		[
			"name",
			"subject",
			"sender",
			"body_html",
			"body_plain",
			"creation",
			"display_name",
			"in_reply_to_mail_name",
			"in_reply_to_mail_type",
			"message_id",
		],
		limit=50,
		start=start,
		order_by=order_by,
	)

	return get_mail_list(mails, "Outgoing Mail")


def get_mail_list(mails, mail_type) -> list:
	"""Returns a list of mails with additional details."""

	for mail in mails[:]:
		mail.mail_type = mail_type
		thread = get_list_thread(mail)
		thread_with_names = [email.name for email in thread]
		mails_in_original_list = [email for email in mails if email.name in thread_with_names]
		if len(mails_in_original_list) > 1:
			latest_mail = max(mails_in_original_list, key=lambda x: x.creation)
			mails_in_original_list.remove(latest_mail)

			for email in mails_in_original_list:
				mails.remove(email)

	for mail in mails:
		mail.latest_content = get_latest_content(mail.body_html, mail.body_plain)
		mail.snippet = get_snippet(mail.latest_content) if mail.latest_content else ""

	return mails


def get_list_thread(mail) -> list:
	"""Returns a list of mails in the thread."""

	thread = []
	processed = set()

	def add_to_thread(mail):
		if mail.name in processed:
			return
		processed.add(mail.name)
		thread.append(mail)

		if mail.in_reply_to_mail_name:
			reply_mail = get_mail_details(mail.in_reply_to_mail_name, mail.in_reply_to_mail_type, False)
			add_to_thread(reply_mail)
		if mail.message_id:
			replica_name = find_replica(mail, mail.mail_type)
			if replica_name:
				replica = get_mail_details(replica_name, reverse_type(mail.mail_type), False)
				add_to_thread(replica)

	add_to_thread(mail)
	return thread


def get_latest_content(html, plain) -> str:
	"""Returns the latest content from the mail."""

	content = html if html else plain
	if content is None:
		return ""

	if is_html(content):
		soup = BeautifulSoup(content, "html.parser")
		blockquote = soup.find("blockquote")
		if blockquote:
			blockquote.extract()
		return soup.get_text(strip=True)

	return content


def get_snippet(content) -> str:
	"""Returns a snippet of the content."""

	content = re.sub(
		r"(?<=[.,])(?=[^\s])", r" ", content
	)  # add space after . and , if not followed by a space
	return " ".join(content.split()[:50])


@frappe.whitelist()
def get_mail_thread(name, mail_type) -> list:
	"""Returns the mail thread for the given mail."""

	mail = get_mail_details(name, mail_type, True)
	mail.mail_type = mail_type

	original_replica = find_replica(mail, mail_type)

	thread = []
	visited = set()

	def get_thread(mail, thread):
		thread.append(mail)
		if mail.name in visited:
			return
		visited.add(mail.name)

		if mail.in_reply_to_mail_name:
			reply_mail = get_mail_details(mail.in_reply_to_mail_name, mail.in_reply_to_mail_type, True)
			get_thread(reply_mail, thread)

		replica = find_replica(mail, mail.mail_type)
		if replica and replica != name:
			replica_type = reverse_type(mail.mail_type)
			replica_mail = get_mail_details(replica, replica_type, True)
			replica_mail.mail_type = replica_type
			get_thread(replica_mail, thread)
		else:
			replies = []
			replies += gather_thread_replies(name)
			if original_replica:
				replies += gather_thread_replies(original_replica)

			for reply in replies:
				if reply.name not in visited:
					get_thread(reply, thread)

	get_thread(mail, thread)
	thread = remove_duplicates_and_sort(thread)
	return thread


def reverse_type(mail_type) -> str:
	"""Returns the reverse mail type."""

	return "Incoming Mail" if mail_type == "Outgoing Mail" else "Outgoing Mail"


def gather_thread_replies(mail_name) -> list:
	"""Gathers all replies in the thread."""

	thread = []
	thread += get_thread_from_replies("Outgoing Mail", mail_name)
	thread += get_thread_from_replies("Incoming Mail", mail_name)
	return thread


def get_thread_from_replies(mail_type, mail_name) -> list:
	"""Returns the thread from the replies."""

	replies = []
	emails = frappe.get_all(mail_type, {"in_reply_to_mail_name": mail_name, "docstatus": 1}, pluck="name")
	for email in emails:
		reply = get_mail_details(email, mail_type, True)
		reply.mail_type = mail_type
		replies.append(reply)

	return replies


def find_replica(mail, mail_type) -> str:
	"""Returns the replica of the mail."""

	replica_type = reverse_type(mail_type)
	return frappe.db.exists(replica_type, {"message_id": mail.message_id})


def remove_duplicates_and_sort(thread) -> list:
	"""Removes duplicates and sorts the thread."""

	seen = set()
	thread = [x for x in thread if x["name"] not in seen and not seen.add(x["name"])]
	thread = [x for x in thread if x["message_id"] not in seen and not seen.add(x["message_id"])]
	thread.sort(key=lambda x: x.creation)
	return thread


def get_mail_details(name: str, type: str, include_all_details: bool = False) -> dict:
	"""Returns the mail details."""

	fields = [
		"name",
		"subject",
		"body_html",
		"body_plain",
		"sender",
		"display_name",
		"creation",
		"modified",
		"message_id",
		"in_reply_to_mail_name",
		"in_reply_to_mail_type",
		"folder",
	]

	mail = frappe.db.get_value(type, name, fields, as_dict=1)
	mail.mail_type = type

	if not include_all_details:
		return mail

	if not mail.get("display_name"):
		mail.display_name = frappe.db.get_value("User", mail.sender, "full_name")

	mail.user_image = frappe.db.get_value("User", mail.sender, "user_image")
	mail.latest_content = get_latest_content(mail.body_html, mail.body_plain)
	mail.to = get_recipients(name, type, "To")
	mail.cc = get_recipients(name, type, "Cc")
	mail.bcc = get_recipients(name, type, "Bcc")
	mail.body_html = extract_email_body(mail.body_html)
	mail.mail_type = type
	return mail


def extract_email_body(html) -> str | None:
	"""Extracts the email body from the html content."""

	if not html:
		return
	soup = BeautifulSoup(html, "html.parser")
	email_body = soup.find("table", class_="email-body")
	if email_body:
		return email_body.find("div").prettify()
	return html


def get_recipients(name, type, recipient_type) -> list:
	"""Returns the recipients of the mail."""

	recipients = frappe.get_all(
		"Mail Recipient",
		{"parent": name, "parenttype": type, "type": recipient_type},
		["email", "display_name", "type"],
	)

	for recipient in recipients:
		if not recipient.display_name:
			recipient.display_name = frappe.db.get_value("User", recipient.email, "full_name")

	return recipients


@frappe.whitelist()
def get_mail_contacts(txt=None) -> list:
	"""Returns the mail contacts for the current user."""

	filters = {"user": frappe.session.user}
	if txt:
		filters["email"] = ["like", f"%{txt}%"]

	contacts = frappe.get_all("Mail Contact", filters=filters, fields=["email"])

	for contact in contacts:
		details = frappe.db.get_value(
			"User", {"email": contact.email}, ["user_image", "full_name", "email"], as_dict=1
		)
		if details:
			contact.update(details)

	return contacts


@frappe.whitelist()
def get_default_outgoing() -> str | None:
	"""Returns default outgoing mailbox."""

	return get_user_default_mail_account(frappe.session.user)


@frappe.whitelist()
def update_draft_mail(
	mail_id: str,
	from_: str,
	to: str | list[str],
	subject: str,
	cc: str | list[str] | None = None,
	bcc: str | list[str] | None = None,
	html: str | None = None,
	attachments: list[dict] | None = None,
	do_submit: bool = False,
):
	"""Update draft mail."""

	display_name, sender = parseaddr(from_)

	doc = frappe.get_doc("Outgoing Mail", mail_id)
	doc.sender = sender
	doc.display_name = display_name
	doc._update_recipients("To", to)
	doc._update_recipients("Cc", cc)
	doc._update_recipients("Bcc", bcc)
	doc.subject = subject
	doc.body_html = html
	doc.save()
	doc._add_attachment(attachments)

	if do_submit:
		doc.submit()
