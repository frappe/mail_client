# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import bcrypt
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import random_string

from mail.agent import create_account_on_agents, delete_account_from_agents, patch_account_on_agents
from mail.utils import get_dmarc_address, normalize_email
from mail.utils.cache import get_aliases_for_user, get_tenant_for_user
from mail.utils.user import has_role, is_system_manager, is_tenant_admin
from mail.utils.validation import (
	is_email_assigned,
	is_subaddressed_email,
	is_valid_email_for_domain,
	validate_domain_is_enabled_and_verified,
	validate_domain_owned_by_tenant,
)


class MailAccount(Document):
	def autoname(self) -> None:
		self.email = self.email.strip().lower()
		self.name = self.email

	def before_validate(self) -> None:
		self.set_tenant()

	def validate(self) -> None:
		self.validate_enabled()
		self.validate_domain()
		self.validate_user()
		self.validate_user_tenant()
		self.validate_tenant_max_accounts()
		self.validate_email()
		self.set_normalized_email()
		self.validate_password()
		self.validate_default_outgoing_email()
		self.validate_display_name()

	def on_update(self) -> None:
		self.clear_cache()

		if self.enabled:
			if self.has_value_changed("enabled") or self.has_value_changed("email"):
				create_account_on_agents(self.email, self.display_name, self.secret)
			elif self.has_value_changed("display_name") or self.has_value_changed("secret"):
				patch_account_on_agents(
					self.email, self.display_name, self.secret, self.get_doc_before_save().secret
				)
		elif self.has_value_changed("enabled"):
			delete_account_from_agents(self.email)

	def on_trash(self) -> None:
		self.clear_cache()

		if self.enabled:
			delete_account_from_agents(self.email)

	def set_tenant(self) -> None:
		"""Sets the tenant based on the domain."""

		if not self.tenant:
			self.tenant = frappe.db.get_value("Mail Domain", self.domain_name, "tenant")

	def validate_enabled(self) -> None:
		"""Validates the enabled field."""

		if self.enabled:
			return

		if alias := frappe.db.exists(
			"Mail Alias", {"enabled": 1, "alias_for_type": self.doctype, "alias_for_name": self.name}
		):
			frappe.throw(
				_("The account is linked to Mail Alias {0}. Please disable it first.").format(
					frappe.bold(alias)
				)
			)

		if frappe.db.exists("Mail Group Member", {"member_type": self.doctype, "member_name": self.name}):
			frappe.throw(_("The account is linked to a Mail Group as a member. Please remove it first."))

	def validate_domain(self) -> None:
		"""Validates the domain."""

		validate_domain_owned_by_tenant(self.domain_name, self.tenant)
		validate_domain_is_enabled_and_verified(self.domain_name)

	def validate_user(self) -> None:
		"""Validates the user."""

		if not has_role(self.user, "Mail User"):
			frappe.throw(_("User {0} does not have Mail User role.").format(frappe.bold(self.user)))

	def validate_user_tenant(self) -> None:
		"""Validates the user tenant."""

		if self.is_new() or self.enabled:
			if self.tenant != get_tenant_for_user(self.user):
				frappe.throw(
					_("Domain {0} and User {1} must belong to the same tenant.").format(
						frappe.bold(self.domain_name), frappe.bold(self.user)
					)
				)

	def validate_tenant_max_accounts(self) -> None:
		"""Validates the Tenant Max Accounts."""

		total_accounts = frappe.db.count("Mail Account", filters={"tenant": self.tenant, "enabled": 1})
		max_accounts = frappe.db.get_value("Mail Tenant", self.tenant, "max_accounts")
		if total_accounts >= max_accounts:
			frappe.throw(
				_("You have reached the maximum limit of {0} accounts for the tenant.").format(
					frappe.bold(max_accounts)
				)
			)

	def validate_email(self) -> None:
		"""Validates the email address."""

		if not self.email:
			frappe.throw(_("Email is mandatory."))
		is_subaddressed_email(self.email, raise_exception=True)
		is_email_assigned(self.email, self.doctype, raise_exception=True)
		is_valid_email_for_domain(self.email, self.domain_name, raise_exception=True)

	def set_normalized_email(self) -> None:
		"""Sets the normalized email."""

		if not self.normalized_email:
			self.normalized_email = normalize_email(self.email)

	def validate_password(self) -> None:
		"""Generates secret if password is changed"""

		if not self.password:
			self.password = random_string(length=20)

		if not self.is_new():
			if previous_doc := self.get_doc_before_save():
				if previous_doc.get_password("password") == self.get_password("password"):
					return

		self.generate_secret()

	def validate_default_outgoing_email(self) -> None:
		"""Validates the default outgoing email."""

		if not self.default_outgoing_email:
			self.default_outgoing_email = self.email
		else:
			if self.default_outgoing_email not in [self.email] + get_aliases_for_user(self.user):
				frappe.throw(_("Default Email must be one of the email addresses assigned to the user."))

	def validate_display_name(self) -> None:
		"""Validates the display name."""

		if self.is_new() and not self.display_name:
			self.display_name = frappe.db.get_value("User", self.user, "full_name")

	def clear_cache(self) -> None:
		"""Clears the Cache."""

		frappe.cache.hdel(f"user|{self.user}", ["account", "default_outgoing_email"])
		frappe.cache.hdel(f"email|{self.email}", "account")

	def generate_secret(self) -> None:
		"""Generates secret from password"""

		password = self.get_password("password").encode("utf-8")
		salt = bcrypt.gensalt()
		self.secret = bcrypt.hashpw(password, salt).decode()


def _create_user_for_mail_account(
	email: str,
	first_name: str,
	last_name: str | None = None,
	password: str | None = None,
	is_admin: bool = False,
) -> str:
	"""Creates a User for Mail Account"""

	if frappe.db.exists("User", {"email": email}):
		frappe.throw(_("User with email {0} already exists.").format(frappe.bold(email)))

	roles = ["Mail User"]
	if is_admin:
		roles.append("Mail Admin")

	return create_user(email, first_name, last_name, password, roles)


def create_user(
	email: str,
	first_name: str,
	last_name: str | None = None,
	password: str | None = None,
	roles: list[str] | None = None,
) -> str:
	"""Creates a User document"""

	user = frappe.new_doc("User")
	user.first_name = first_name
	user.last_name = last_name
	user.username = email
	user.email = email
	user.owner = email
	user.send_welcome_email = 0
	if roles:
		user.append_roles(*roles)
	if password:
		user.new_password = password
	user.insert(ignore_permissions=True)

	return user.name


def _add_user_to_tenant(tenant: str, user: str, is_admin: bool) -> None:
	"""Adds a User to a Tenant"""

	tenant = frappe.get_doc("Mail Tenant", tenant)
	tenant.add_member(user, is_admin)


def create_mail_account(
	tenant: str,
	email: str,
	first_name: str,
	last_name: str | None = None,
	password: str | None = None,
	is_admin: bool = False,
) -> "MailAccount":
	"""Creates a Mail Account"""

	if frappe.db.exists("Mail Account", email):
		frappe.throw(_("Mail Account {0} already exists.").format(frappe.bold(email)))

	user = _create_user_for_mail_account(email, first_name, last_name, password, is_admin)
	_add_user_to_tenant(tenant, user, is_admin)
	account = frappe.new_doc("Mail Account")
	account.domain_name = email.split("@")[1]
	account.user = user
	account.insert(ignore_permissions=True)

	return account


def create_dmarc_account(tenant: str) -> None:
	"""Creates a DMARC account"""

	frappe.flags.ignore_domain_validation = True
	create_mail_account(tenant=tenant, email=get_dmarc_address(), first_name="DMARC")


def has_permission(doc: "Document", ptype: str, user: str | None = None) -> bool:
	if doc.doctype != "Mail Account":
		return False

	user = user or frappe.session.user

	if is_system_manager(user):
		return True

	if is_tenant_admin(doc.tenant, user):
		return True

	if has_role(user, "Mail User"):
		return user == doc.user

	return False


def get_permission_query_condition(user: str | None = None) -> str:
	user = user or frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		if tenant := get_tenant_for_user(user):
			return f"(`tabMail Account`.`tenant` = {frappe.db.escape(tenant)})"

	if has_role(user, "Mail User"):
		return f"(`tabMail Account`.`user` = {frappe.db.escape(user)})"

	return "1=0"
