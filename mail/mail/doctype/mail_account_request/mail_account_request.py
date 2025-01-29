# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import random

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, get_url, nowdate, random_string

from mail.utils.cache import get_tenant_for_user
from mail.utils.user import has_role, is_mail_tenant_admin, is_system_manager


class MailAccountRequest(Document):
	def validate(self) -> None:
		self.validate_role()
		self.validate_tenant()

	def before_insert(self) -> None:
		self.set_request_key()

		if not self.invited_by:
			self.set_otp()

	def after_insert(self) -> None:
		if self.send_email:
			self.send_verification_email()

	def validate_role(self) -> None:
		if not self.role:
			frappe.throw(_("Role is mandatory."))

		if self.role not in ["Mail User", "Mail Admin"]:
			frappe.throw(_("Invalid role. Please select a valid role."))

	def validate_tenant(self) -> None:
		if self.role == "Mail Admin":
			self.tenant = None
		elif self.role == "Mail User":
			if not self.tenant:
				frappe.throw(_("Tenant is mandatory for Mail User role."))

	def set_request_key(self) -> None:
		"""Sets a random key for the request."""

		self.request_key = random_string(32)

	def set_otp(self) -> None:
		"""Sets a random 5-digit OTP for the request."""

		self.otp = random.randint(10000, 99999)

	@frappe.whitelist()
	def send_verification_email(self) -> None:
		"""Send verification email to the user."""

		link = get_url() + "/signup/" + self.request_key
		args = {
			"link": link,
			"otp": self.otp,
			"image_path": "https://frappe.io/files/Frappe-black.png",
		}

		if self.invited_by:
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


def expire_mail_account_requests() -> None:
	"""Called by scheduler to expire mail account requests older than 7 days."""

	frappe.db.set_value(
		"Mail Account Request",
		{"is_expired": 0, "creation": ["<", add_days(nowdate(), -7)]},
		"is_expired",
		1,
	)


def has_permission(doc: "Document", ptype: str, user: str) -> bool:
	if doc.doctype != "Mail Account Request":
		return False

	if is_system_manager(user):
		return True

	if is_mail_tenant_admin(doc.tenant, user):
		if ptype in ("create", "read", "write"):
			return True

	return False


def get_permission_query_condition(user: str | None = None) -> str:
	if not user:
		user = frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		if tenant := get_tenant_for_user(user):
			return f'(`tabMail Account Request`.`tenant` = "{tenant}")'

	return "1=0"
