# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import random_string

from mail.utils.cache import get_tenant_for_user
from mail.utils.dns import verify_dns_record
from mail.utils.user import has_role, is_system_manager, is_tenant_admin


class MailDomainRequest(Document):
	def before_validate(self) -> None:
		if self.is_new():
			self.set_user_and_tenant()

	def validate(self) -> None:
		if self.is_new():
			self.validate_domain_name()

		self.validate_user_and_tenant()

	def before_insert(self) -> None:
		self.set_verification_key()

	def set_user_and_tenant(self) -> None:
		"""Set the user and tenant"""

		user = frappe.session.user

		if is_system_manager(user):
			if not self.user:
				frappe.throw(_("User is required"))
			elif not self.tenant:
				frappe.throw(_("Tenant is required"))
		else:
			self.user = user
			self.tenant = get_tenant_for_user(user)

	def validate_domain_name(self) -> None:
		"""Validates the domain name"""

		domain_regex = r"^(?!:\/\/)([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$"
		if re.fullmatch(domain_regex, self.domain_name) is None:
			frappe.throw(_("Invalid domain name"))

		if frappe.db.exists("Mail Domain", {"domain_name": self.domain_name}):
			frappe.throw(_("Domain {0} already registered.").format(frappe.bold(self.domain_name)))

	def validate_user_and_tenant(self) -> None:
		"""Validates the user and tenant"""

		if not is_tenant_admin(self.tenant, self.user):
			frappe.throw(_("User must be an admin of the tenant"))

	def set_verification_key(self) -> None:
		"""Set the verification key"""

		self.verification_key = "frappe-mail-verification=" + random_string(48)

	@frappe.whitelist()
	def verify_and_create_domain(self, save: bool = False) -> bool:
		"""Verifies the domain and creates the mail domain"""

		if self.is_verified:
			frappe.throw(_("Domain is already verified and created."))

		self.is_verified = 0
		if verify_dns_record(self.domain_name, "TXT", self.verification_key):
			self.is_verified = 1
			frappe.msgprint(_("Domain Verification Successful"), indicator="green", alert=True)
			self.create_domain()
		else:
			frappe.msgprint(_("Domain Verification Failed"), indicator="red", alert=True)

		if save:
			self.save()

		return bool(self.is_verified)

	def create_domain(self) -> str:
		"""Create the mail domain"""

		domain = frappe.new_doc("Mail Domain")
		domain.tenant = self.tenant
		domain.domain_name = self.domain_name
		domain.insert(ignore_permissions=True)

		return domain.name


def has_permission(doc: "Document", ptype: str, user: str) -> bool:
	if doc.doctype != "Mail Domain Request":
		return False

	if is_system_manager(user):
		return True

	if is_tenant_admin(doc.tenant, user):
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
			return f'(`tabMail Domain Request`.`tenant` = "{tenant}")'

	return "1=0"
