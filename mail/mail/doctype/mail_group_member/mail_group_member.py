# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from mail.mail.doctype.mail_agent_request_log.mail_agent_request_log import (
	create_member_on_agents,
	delete_member_from_agents,
)


class MailGroupMember(Document):
	@property
	def member_is_group(self) -> bool:
		"""Return True if the member is a mail group"""

		return self.member_type == "Mail Group"

	def validate(self) -> None:
		self.validate_member_name()

	def validate_member_name(self) -> None:
		"""Validate if the member name is not the same as the mail group"""

		if self.mail_group == self.member_name:
			if self.member_type == "Mail Group":
				frappe.throw(_("Mail Group cannot be a member of itself"))
			else:
				frappe.throw(_("Member cannot be the same as the Mail Group"))

	def after_insert(self) -> None:
		create_member_on_agents(self.mail_group, self.member_name, self.member_is_group)

	def on_trash(self) -> None:
		delete_member_from_agents(self.mail_group, self.member_name, self.member_is_group)


def on_doctype_update() -> None:
	frappe.db.add_unique(
		"Mail Group Member",
		["mail_group", "member_name"],
		constraint_name="unique_mail_group_member",
	)
