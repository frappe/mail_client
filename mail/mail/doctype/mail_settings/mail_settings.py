# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.utils.validation import is_valid_host


class MailSettings(Document):
	def validate(self) -> None:
		self.validate_root_domain_name()
		self.validate_dns_provider()
		self.validate_spf_host()

	def on_update(self) -> None:
		frappe.cache.delete_value("smtp_limits")
		frappe.cache.delete_value("imap_limits")
		frappe.cache.delete_value("root_domain_name")

		if self.has_value_changed("root_domain_name"):
			create_dmarc_dns_record_for_external_domains()

	def validate_root_domain_name(self) -> None:
		"""Validates the Root Domain Name."""

		self.root_domain_name = self.root_domain_name.lower()

		if self.has_value_changed("root_domain_name"):
			frappe.db.set_value("DNS Record", {"is_verified": 1}, "is_verified", 0)

			if self.get_doc_before_save().get("root_domain_name"):
				dns_record_list_link = f'<a href="/app/dns-record">{_("DNS Records")}</a>'
				frappe.msgprint(
					_("Please verify the {0} for the new {1} to ensure proper email authentication.").format(
						dns_record_list_link, frappe.bold("Root Domain Name")
					)
				)

	def validate_dns_provider(self) -> None:
		"""Validates the DNS Provider."""

		if self.dns_provider and not self.dns_provider_token:
			frappe.throw(_("Please set the DNS Provider Token."))

	def validate_spf_host(self) -> None:
		"""Validates the SPF Host."""

		if not self.has_value_changed("spf_host"):
			return

		from mail.mail.doctype.mail_agent.mail_agent import create_or_update_spf_dns_record

		self.spf_host = self.spf_host.lower()
		if not is_valid_host(self.spf_host):
			msg = _(
				"SPF Host {0} is invalid. It can be alphanumeric but should not contain spaces or special characters, excluding underscores."
			).format(frappe.bold(self.spf_host))
			frappe.throw(msg)

		previous_doc = self.get_doc_before_save()
		if previous_doc and previous_doc.spf_host:
			if spf_dns_record := frappe.db.exists(
				"DNS Record", {"host": previous_doc.spf_host, "type": "TXT"}
			):
				frappe.delete_doc("DNS Record", spf_dns_record, ignore_permissions=True)

		create_or_update_spf_dns_record(self.spf_host)


def create_dmarc_dns_record_for_external_domains() -> None:
	"""Creates the DMARC DNS Record for external domains."""

	from mail.mail.doctype.dns_record.dns_record import create_or_update_dns_record

	frappe.flags.enqueue_dns_record_update = True
	create_or_update_dns_record(
		host="*._report._dmarc",
		type="TXT",
		value="v=DMARC1",
		category="Server Record",
	)


def validate_mail_settings() -> None:
	"""Validates the mandatory fields in the Mail Settings."""

	mail_settings = frappe.get_doc("Mail Settings")
	mandatory_fields = [
		"root_domain_name",
		"spf_host",
		"default_ttl",
	]

	for field in mandatory_fields:
		if not mail_settings.get(field):
			field_label = frappe.get_meta("Mail Settings").get_label(field)
			frappe.throw(_("Please set the {0} in the Mail Settings.").format(frappe.bold(field_label)))
