# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import random

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, get_url, nowdate, random_string, validate_email_address

from mail.mail.doctype.mail_account.mail_account import create_mail_account
from mail.utils.cache import get_tenant_for_user
from mail.utils.user import has_role, is_system_manager, is_tenant_admin
from mail.utils.validation import (
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
	validate_domain_owned_by_tenant,
)

# todo:
# clean up form
# clean up create_account
# make role => is_admin
# fix email styles
# fix email frappe logo
# create mail account after sign up


class MailAccountRequest(Document):
	def validate(self) -> None:
		self.validate_role()
		self.validate_email()

		if self.is_new():
			if self.is_invite:
				self.validate_invited_by_and_tenant()
				self.validate_domain()
				self.validate_account()

			else:
				self.validate_non_invite()

	def before_insert(self) -> None:
		self.set_request_key()
		self.set_otp()

	def after_insert(self) -> None:
		if self.send_email:
			self.send_verification_email()

	def validate_role(self) -> None:
		"""Validates the role."""

		if not self.role:
			frappe.throw(_("Role is mandatory."))

		if self.role not in ["Mail User", "Mail Admin"]:
			frappe.throw(_("Invalid role. Please select a valid role."))

	def validate_email(self) -> None:
		"""Validates email if needed."""

		if self.send_email and not self.email:
			frappe.throw(_("Email is required to send invite"))

		self.email = self.email.strip().lower()
		validate_email_address(self.email, True)

	def validate_non_invite(self) -> None:
		"""Validates self sign up."""

		if frappe.db.exists("User", self.email):
			frappe.throw(_("User {0} is already registered.").format(self.email))

		self.role = "Mail Admin"
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

		if not is_valid_email_for_domain(self.account, self.domain_name):
			frappe.throw(
				_("Account domain {0} does not match with domain {1}.").format(
					frappe.bold(self.account.split("@")[1]), frappe.bold(self.domain_name)
				)
			)

	def set_request_key(self) -> None:
		"""Sets a random key for the request."""

		self.request_key = random_string(32)

	def set_otp(self) -> None:
		"""Sets a random 5-digit OTP for the request."""

		self.otp = random.randint(10000, 99999)

	@frappe.whitelist()
	def send_verification_email(self) -> None:
		"""Send verification email to the user."""

		link = get_url() + "/mail/signup/" + self.request_key
		args = {
			"link": link,
			"otp": self.otp,
			"image_path": "https://frappe.io/files/Frappe-black.png",
		}

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
			role=self.role,
		)


def expire_mail_account_requests() -> None:
	"""Called by scheduler to expire mail account requests older than 7 days."""

	frappe.db.set_value(
		"Mail Account Request",
		{"is_expired": 0, "creation": ["<", add_days(nowdate(), -7)]},
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
