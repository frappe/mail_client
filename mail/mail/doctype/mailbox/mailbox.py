# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.utils.cache import delete_cache
from mail.utils.user import has_role, is_system_manager
from mail.utils.validation import (
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
)


class Mailbox(Document):
	def autoname(self) -> None:
		self.email = self.email.strip().lower()
		self.name = self.email

	def validate(self) -> None:
		self.validate_domain()
		self.validate_user()
		self.validate_email()
		self.validate_display_name()
		self.validate_default_mailbox()

	def on_update(self) -> None:
		delete_cache(f"user|{self.user}")

	def on_trash(self) -> None:
		self.validate_against_mail_alias()
		delete_cache(f"user|{self.user}")

	def validate_domain(self) -> None:
		"""Validates the domain."""

		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_user(self) -> None:
		"""Validates the user."""

		if not self.user:
			if self.postmaster:
				self.user = "Administrator"
			else:
				frappe.throw(_("User is mandatory."))

		if not has_role(self.user, "Mailbox User") and not is_system_manager(self.user):
			frappe.throw(_("User {0} does not have Mailbox User role.").format(frappe.bold(self.user)))

	def validate_email(self) -> None:
		"""Validates the email address."""

		is_valid_email_for_domain(self.email, self.domain_name, raise_exception=True)

	def validate_display_name(self) -> None:
		"""Validates the display name."""

		if self.is_new() and not self.display_name:
			self.display_name = frappe.db.get_value("User", self.user, "full_name")

	def validate_default_mailbox(self) -> None:
		"""Validates the default mailbox."""

		if not self.outgoing or self.postmaster:
			self.is_default = 0
			return

		filters = {
			"user": self.user,
			"is_default": 1,
			"outgoing": 1,
			"name": ["!=", self.name],
		}
		has_default_mailbox = frappe.db.exists("Mailbox", filters)

		if self.is_default:
			if has_default_mailbox:
				frappe.db.set_value("Mailbox", filters, "is_default", 0)
		elif not has_default_mailbox:
			self.is_default = 1

	def validate_against_mail_alias(self) -> None:
		"""Validates if the mailbox is linked with an active Mail Alias."""

		MA = frappe.qb.DocType("Mail Alias")
		MAM = frappe.qb.DocType("Mail Alias Mailbox")

		data = (
			frappe.qb.from_(MA)
			.left_join(MAM)
			.on(MA.name == MAM.parent)
			.select(MA.name)
			.where((MA.enabled == 1) & (MAM.mailbox == self.email))
			.limit(1)
		).run(pluck="name")

		if data:
			frappe.throw(
				_("Mailbox {0} is linked with active Mail Alias {1}.").format(
					frappe.bold(self.name), frappe.bold(data[0])
				)
			)


def create_postmaster_mailbox(domain_name: str) -> "Mailbox":
	"""Creates a postmaster mailbox for the domain."""

	email = f"postmaster@{domain_name}"
	frappe.flags.ingore_domain_validation = True
	postmaster = create_mailbox(
		domain_name,
		email,
		display_name="Postmaster",
		incoming=False,
		outgoing=True,
		postmaster=True,
	)
	return postmaster


def create_mailbox(
	domain_name: str,
	email: str,
	display_name: str | None = None,
	user: str | None = None,
	incoming: bool = True,
	outgoing: bool = True,
	postmaster: bool = False,
) -> "Mailbox":
	"""Creates a user and mailbox if not exists."""

	user = user or email

	if not frappe.db.exists("Mailbox", email):
		if not frappe.db.exists("User", user) and not postmaster:
			mailbox_user = frappe.new_doc("User")
			mailbox_user.email = user
			mailbox_user.username = user
			mailbox_user.first_name = display_name
			mailbox_user.user_type = "System User"
			mailbox_user.send_welcome_email = 0
			mailbox_user.append_roles("Mailbox User")
			mailbox_user.insert(ignore_permissions=True)

		mailbox = frappe.new_doc("Mailbox")
		mailbox.domain_name = domain_name
		mailbox.email = email
		mailbox.display_name = display_name

		if not postmaster:
			mailbox.user = user

		mailbox.incoming = incoming
		mailbox.outgoing = outgoing
		mailbox.postmaster = postmaster
		mailbox.insert(ignore_permissions=True)

		return mailbox

	return frappe.get_doc("Mailbox", email)


def get_permission_query_condition(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if is_system_manager(user):
		return ""

	return f"(`tabMailbox`.`user` = {frappe.db.escape(user)})"


def has_permission(doc: "Document", ptype: str, user: str) -> bool:
	if doc.doctype != "Mailbox":
		return False

	return (user == doc.user) or is_system_manager(user)


@frappe.whitelist()
def delete_incoming_mails(mailbox: str) -> None:
	"""Deletes the incoming mails for the given mailbox."""

	frappe.only_for("System Manager")

	if mailbox:
		frappe.db.delete("Incoming Mail", {"receiver": mailbox})


@frappe.whitelist()
def delete_outgoing_mails(mailbox: str) -> None:
	"""Deletes the outgoing mails for the given mailbox."""

	frappe.only_for("System Manager")

	if mailbox:
		frappe.db.delete("Outgoing Mail", {"sender": mailbox})
