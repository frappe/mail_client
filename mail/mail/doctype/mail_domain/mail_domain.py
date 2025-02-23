# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

from mail.agent import create_domain_on_agents, delete_domain_from_agents
from mail.mail.doctype.dkim_key.dkim_key import create_dkim_key
from mail.mail.doctype.mail_account.mail_account import create_dmarc_account
from mail.utils import get_dkim_host, get_dkim_selector, get_dmarc_address
from mail.utils.cache import get_root_domain_name, get_tenant_for_user
from mail.utils.dns import verify_dns_record
from mail.utils.user import get_user_linked_domains, has_role, is_system_manager, is_tenant_admin


class MailDomain(Document):
	def autoname(self) -> None:
		self.domain_name = self.domain_name.strip().lower()
		self.name = self.domain_name

	def validate(self) -> None:
		if self.is_new():
			self.validate_is_subdomain()
			self.validate_is_root_domain()

		self.validate_tenant_max_domains()
		self.validate_dkim_rsa_key_size()
		self.validate_newsletter_retention()
		self.validate_is_verified()

		if self.is_new() or self.has_value_changed("dkim_rsa_key_size"):
			create_dkim_key(self.domain_name, cint(self.dkim_rsa_key_size))
			self.refresh_dns_records(do_not_save=True)

	def after_insert(self) -> None:
		create_domain_on_agents(domain_name=self.domain_name)

		if self.is_root_domain:
			create_dmarc_account(self.tenant)

	def on_update(self) -> None:
		self.clear_cache()

	def on_trash(self) -> None:
		if frappe.session.user != "Administrator":
			frappe.throw(_("Only Administrator can delete Mail Domain."))

		self.clear_cache()
		delete_domain_from_agents(domain_name=self.domain_name)

	def validate_is_subdomain(self) -> None:
		"""Validates the Is Subdomain field."""

		if len(self.domain_name.split(".")) > 2:
			self.is_subdomain = 1

	def validate_is_root_domain(self) -> None:
		"""Validates the Is Root Domain field."""

		self.is_root_domain = 1 if self.domain_name == get_root_domain_name() else 0

	def validate_tenant_max_domains(self) -> None:
		"""Validates the Tenant Max Domains."""

		total_domains = frappe.db.count("Mail Domain", filters={"tenant": self.tenant, "enabled": 1})
		max_domains = frappe.db.get_value("Mail Tenant", self.tenant, "max_domains")
		if total_domains >= max_domains:
			frappe.throw(
				_("You have reached the maximum limit of {0} domains for the tenant.").format(
					frappe.bold(max_domains)
				)
			)

	def validate_dkim_rsa_key_size(self) -> None:
		"""Validates the DKIM Key Size."""

		if not self.dkim_rsa_key_size:
			self.dkim_rsa_key_size = frappe.db.get_single_value(
				"Mail Settings", "default_dkim_rsa_key_size", cache=True
			)

	def validate_newsletter_retention(self) -> None:
		"""Validates the Newsletter Retention."""

		if self.newsletter_retention:
			if self.newsletter_retention < 1:
				frappe.throw(_("Newsletter Retention must be greater than 0."))

			max_newsletter_retention = frappe.db.get_single_value(
				"Mail Settings", "max_newsletter_retention", cache=True
			)
			if self.newsletter_retention > max_newsletter_retention:
				frappe.throw(
					_("Newsletter Retention must be less than or equal to {0}.").format(
						frappe.bold(max_newsletter_retention)
					)
				)
		else:
			self.newsletter_retention = frappe.db.get_single_value(
				"Mail Settings", "default_newsletter_retention", cache=True
			)

	def validate_is_verified(self) -> None:
		"""Validates the Is Verified field."""

		if not self.enabled:
			self.is_verified = 0

	@frappe.whitelist()
	def refresh_dns_records(self, do_not_save: bool = False) -> None:
		"""Refreshes the DNS Records."""

		if not has_permission(self, "write"):
			frappe.throw(_("You do not have permission to refresh DNS Records."))

		self.is_verified = 0
		self.dns_records.clear()

		for record in get_dns_records(self.domain_name):
			self.append("dns_records", record)

		if not do_not_save:
			self.save(ignore_permissions=True)
			frappe.msgprint(_("DNS Records refreshed successfully."), indicator="green", alert=True)

	@frappe.whitelist()
	def verify_dns_records(self, do_not_save: bool = False) -> bool:
		"""Verifies the DNS Records."""

		if not has_permission(self, "write"):
			frappe.throw(_("You do not have permission to verify DNS Records."))

		errors = []
		for record in self.dns_records:
			if not verify_dns_record(record.host, record.type, record.value):
				errors.append(
					_("Row #{0}: Failed to verify {1} : {2}.").format(
						record.idx, frappe.bold(record.type), frappe.bold(record.host)
					)
				)

		if not errors:
			self.is_verified = 1
			frappe.msgprint(_("DNS Records verified successfully."), indicator="green", alert=True)
		else:
			self.is_verified = 0
			frappe.msgprint(errors, title="DNS Verification Failed", indicator="red", as_list=True)

		if not do_not_save:
			self.save(ignore_permissions=True)

		return bool(self.is_verified)

	@frappe.whitelist()
	def rotate_dkim_keys(self) -> None:
		"""Rotates the DKIM Keys."""

		if not has_permission(self, "write"):
			frappe.throw(_("You do not have permission to rotate DKIM Keys."))

		create_dkim_key(self.domain_name, cint(self.dkim_rsa_key_size))
		frappe.msgprint(_("DKIM Keys rotated successfully."), indicator="green", alert=True)

	def clear_cache(self) -> None:
		"""Clears the Cache."""

		frappe.cache.hdel(f"tenant|{self.tenant}", "domains")

		if self.has_value_changed("tenant"):
			if previous_doc := self.get_doc_before_save():
				if previous_doc.tenant:
					frappe.cache.hdel(f"tenant|{previous_doc.tenant}", "domains")


def get_dns_records(domain_name: str) -> list[dict]:
	"""Returns the DNS Records for the given domain."""

	records = []
	mail_settings = frappe.get_cached_doc("Mail Settings")

	# SPF Record
	records.append(
		{
			"category": "Sending Record",
			"type": "TXT",
			"host": domain_name,
			"value": f"v=spf1 include:{mail_settings.spf_host}.{mail_settings.root_domain_name} ~all",
			"ttl": mail_settings.default_ttl,
		},
	)

	# DKIM Record
	records.append(
		{
			"category": "Sending Record",
			"type": "CNAME",
			"host": f"{get_dkim_selector('rsa')}._domainkey.{domain_name}",
			"value": f"{get_dkim_host(domain_name, 'rsa')}._domainkey.{mail_settings.root_domain_name}.",
			"ttl": mail_settings.default_ttl,
		}
	)

	# DMARC Record
	dmarc_address = get_dmarc_address()
	records.append(
		{
			"category": "Sending Record",
			"type": "TXT",
			"host": f"_dmarc.{domain_name}",
			"value": f"v=DMARC1; p=reject; rua=mailto:{dmarc_address}; ruf=mailto:{dmarc_address}; fo=1; aspf=s; adkim=s; pct=100;",
			"ttl": mail_settings.default_ttl,
		}
	)

	# MX Record(s)
	if inbound_agent_groups := frappe.db.get_all(
		"Mail Agent Group",
		filters={"enabled": 1, "inbound": 1},
		fields=["agent_group", "priority"],
		order_by="priority asc",
	):
		for group in inbound_agent_groups:
			records.append(
				{
					"category": "Receiving Record",
					"type": "MX",
					"host": domain_name,
					"value": f"{group.agent_group.split(':')[0]}.",
					"priority": group.priority,
					"ttl": mail_settings.default_ttl,
				}
			)

	return records


def has_permission(doc: "Document", ptype: str, user: str | None = None) -> bool:
	if doc.doctype != "Mail Domain":
		return False

	user = user or frappe.session.user

	if is_system_manager(user):
		return True

	if is_tenant_admin(doc.tenant, user):
		if ptype in ("read", "write"):
			return True

	return False


def get_permission_query_condition(user: str | None = None) -> str:
	user = user or frappe.session.user

	if is_system_manager(user):
		return ""

	if has_role(user, "Mail Admin"):
		if tenant := get_tenant_for_user(user):
			return f"(`tabMail Domain`.`tenant` = {frappe.db.escape(tenant)})"

	if has_role(user, "Mail User"):
		if linked_domains := get_user_linked_domains(user):
			return f'(`tabMail Domain`.`domain_name` IN ({", ".join([frappe.db.escape(domain) for domain in linked_domains])}))'

	return "1=0"
