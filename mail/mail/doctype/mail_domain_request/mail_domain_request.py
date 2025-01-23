# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.utils import random_string


class MailDomainRequest(Document):
	def before_insert(self):
		self.verification_key = random_string(48)
