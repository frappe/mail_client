# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import random

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, get_url, nowdate, random_string, validate_email_address

from mail.mail.doctype.mail_account.mail_account import create_mail_account
from mail.utils import generate_otp
from mail.utils.cache import get_tenant_for_user
from mail.utils.user import has_role, is_system_manager, is_tenant_admin
from mail.utils.validation import (
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
	validate_domain_owned_by_tenant,
)


class MailAccountRequest(Document):
	def validate(self) -> None:
		self.validate_email()

		if self.is_new():
			self.set_ip_address()

			if self.is_invite:
				self.validate_invited_by_and_tenant()
				self.validate_domain()
				self.validate_account()
			else:
				self.validate_non_invite()

	def before_insert(self) -> None:
		self.set_request_key()
		if not self.is_invite:
			self.set_otp()

	def after_insert(self) -> None:
		if self.send_invite:
			self.send_verification_email()

	def validate_email(self) -> None:
		"""Validates email if needed."""

		if self.email:
			self.email = self.email.strip().lower()
			validate_email_address(self.email, True)

	def set_ip_address(self) -> None:
		"""Sets the IP address of the request."""

		self.ip_address = frappe.local.request_ip

	def validate_non_invite(self) -> None:
		"""Validates self sign up."""

		if frappe.db.exists("User", {"email": self.email}):
			frappe.throw(_("User {0} is already registered.").format(self.email))

		self.is_admin = 1
		self.invited_by = None
		self.tenant = None
		self.domain_name = None
		self.account = None

	def validate_invited_by_and_tenant(self) -> None:
		"""Validates the invited_by and tenant fields."""

		user = frappe.session.user
		if is_system_manager(user):
			if not self.invited_by:
				frappe.throw(_("Invited By is required"))
			elif not self.tenant:
				frappe.throw(_("Tenant is required"))
		else:
			self.invited_by = user
			self.tenant = get_tenant_for_user(user)

		if not is_tenant_admin(self.tenant, self.invited_by):
			frappe.throw(
				_("User {0} is not authorized to invite users to the tenant.").format(
					frappe.bold(self.invited_by)
				)
			)

	def validate_domain(self) -> None:
		"""Validates the domain."""

		if not self.domain_name:
			frappe.throw(_("Domain is mandatory."))

		validate_domain_owned_by_tenant(self.domain_name, self.tenant)
		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_account(self) -> None:
		"""Validates the account."""

		self.account = self.account.strip().lower()
		validate_email_address(self.account, True)

		if not is_valid_email_for_domain(self.account, self.domain_name):
			frappe.throw(
				_("Account domain {0} does not match with domain {1}.").format(
					frappe.bold(self.account.split("@")[1]), frappe.bold(self.domain_name)
				)
			)

		if frappe.db.exists("User", {"email": self.account}):
			frappe.throw(_("User {0} is already registered.").format(self.account))

	def validate_expired(self) -> None:
		"""Forbids action if the request has expired."""

		if self.is_expired:
			frappe.throw(_("This request has expired. Please create a new one."))

	def set_request_key(self) -> None:
		"""Sets a random key for the request."""

		self.request_key = random_string(32)

	def set_otp(self) -> None:
		"""Sets a random 5-digit OTP for the request."""

		if not self.name:
			self.set_new_name()

		self.otp = "12345" if frappe.conf.developer_mode else str(generate_otp())
		frappe.cache.set_value(
			f"account_request_otp_hash:{self.name}",
			frappe.utils.sha256_hash(str(self.otp)),
			expires_in_sec=60 * 10,
		)

	@frappe.whitelist()
	def send_verification_email(self) -> None:
		"""Send verification email to the user."""

		if not self.email:
			frappe.throw(_("Email is required to send invite"))

		self.validate_expired()

		link = get_url() + "/mail/signup/" + self.request_key
		args = {"link": link, "otp": self.otp}

		if self.is_invite and self.invited_by:
			subject = _("You have been invited by {0} to join Frappe Mail").format(self.invited_by)
			template = "invite_signup"
			tenant_name = frappe.db.get_value("Mail Tenant", self.tenant, "tenant_name")
			args.update({"invited_by": self.invited_by, "tenant": tenant_name})
		else:
			subject = _("{0} - OTP for Frappe Mail Account Verification").format(self.otp)
			template = "self_signup"

		frappe.sendmail(
			recipients=self.email,
			subject=subject,
			template=template,
			args=args,
			now=True,
		)
		frappe.msgprint(_("Verification email sent successfully."), indicator="green", alert=True)

	@frappe.whitelist()
	def force_verify_and_create_account(self, first_name: str, last_name: str, password: str) -> None:
		"""Force verify and create account for invited user."""

		self.validate_expired()

		if not self.is_invite:
			frappe.throw(_("This method can only be called for invited users."))

		if self.is_verified:
			frappe.throw(_("Account is already verified and created."))

		user = frappe.session.user
		if not is_system_manager(user) and not is_tenant_admin(self.tenant, user):
			frappe.throw(_("You are not authorized to perform this action."))

		self.db_set("is_verified", 1)
		self.create_account(first_name, last_name, password)

	def create_account(self, first_name: str, last_name: str, password: str) -> None:
		"""Create mail account for the user."""

		if not self.is_verified:
			frappe.throw(_("Please verify the email address first."))

		create_mail_account(
			tenant=self.tenant,
			email=self.account,
			first_name=first_name,
			last_name=last_name,
			password=password,
			is_admin=self.is_admin,
		)


def expire_mail_account_requests() -> None:
	"""Called by scheduler to expire mail account requests older than 2 days."""

	frappe.db.set_value(
		"Mail Account Request",
		{"is_expired": 0, "creation": ["<", add_days(nowdate(), -2)]},
		"is_expired",
		1,
	)


def has_permission(doc: "Document", ptype: str, user: str | None = None) -> bool:
	if doc.doctype != "Mail Account Request":
		return False

	user = user or frappe.session.user

	if is_system_manager(user):
		return True

	if is_tenant_admin(doc.tenant, user):
		if ptype in ("create", "read", "write"):
			return True

	return False


def get_permission_query_condition(user: str | None = None) -> str:
	user = user or frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		if tenant := get_tenant_for_user(user):
			return f"(`tabMail Account Request`.`tenant` = {frappe.db.escape(tenant)})"

	return "1=0"
