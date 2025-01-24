# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import random_string

from mail.utils.dns import verify_dns_record


class MailDomainRequest(Document):
	def before_insert(self):
		self.verification_key = random_string(48)

	@frappe.whitelist()
	def verify_key(self):
		self.is_verified = verify_dns_record(self.domain_name, "TXT", self.verification_key)
		if self.is_verified:
			self.create_domain()
		return self.is_verified

	def create_domain(self):
		domain = frappe.new_doc("Mail Domain")
		domain.domain_name = self.domain_name
		domain.mail_tenant = self.mail_tenant
		domain.verified = self.is_verified
		domain.insert()
		return domain.name
