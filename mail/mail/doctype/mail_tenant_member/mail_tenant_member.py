# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.utils.user import has_role


class MailTenantMember(Document):
	def validate(self):
		self.validate_user()

	def validate_user(self):
		if not has_role(self.user, ["Mail Admin", "Mail User"]):
			frappe.throw(
				_("User {0} does not have Mail Admin or Mail User role.").format(frappe.bold(self.user))
			)
