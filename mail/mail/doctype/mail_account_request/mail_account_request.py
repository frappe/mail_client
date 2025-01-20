# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import random

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_url, random_string


class MailAccountRequest(Document):
	def before_insert(self):
		if not self.tenant:
			self.tenant = self.email

		if not self.request_key:
			self.request_key = random_string(32)

		if not (self.otp or self.invited_by):
			self.otp = random.randint(10000, 99999)

	def after_insert(self):
		if self.send_email:
			self.send_verification_email()

	@frappe.whitelist()
	def send_verification_email(self):
		link = get_url() + "/signup/" + self.request_key
		args = {
			"link": link,
			"otp": self.otp,
			"image_path": "https://github.com/frappe/gameplan/assets/9355208/447035d0-0686-41d2-910a-a3d21928ab94",
		}

		if self.invited_by:
			subject = f"You have been invited by {self.invited_by} to join Frappe Mail"
			template = "invite_signup"
			args.update({"invited_by": self.invited_by, "tenant": self.tenant})

		else:
			subject = f"{self.otp} - OTP for Frappe Mail Account Verification"
			template = "self_signup"

		frappe.sendmail(
			recipients=self.email,
			subject=subject,
			template=template,
			args=args,
			now=True,
		)
		frappe.msgprint(_("Verification mail sent successfully."), indicator="green", alert=True)
