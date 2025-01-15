# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import random

import frappe
from frappe.model.document import Document
from frappe.utils import get_url, random_string


class MailAccountRequest(Document):
	def before_insert(self):
		if not self.tenant:
			self.tenant = self.email

		if not self.request_key:
			self.request_key = random_string(32)

		if not self.otp:
			self.otp = random.randint(10000, 99999)

	def after_insert(self):
		if self.send_email:
			self.send_verification_email()

	@frappe.whitelist()
	def send_verification_email(self):
		return
		# url = self.get_verification_url()

		subject = f"{self.otp} - OTP for Frappe Mail Account Verification"
		args = {}
		sender = ""

		if not self.invited_by:
			subject = "Verify your email for Frappe"

		else:
			subject = f"You are invited by {self.invited_by} to join Frappe Cloud"

		args.update(
			{
				"invited_by": self.invited_by,
				# "link": url,
				"otp": self.otp,
			}
		)
		if not args.get("image_path"):
			args.update(
				{
					"image_path": "https://github.com/frappe/gameplan/assets/9355208/447035d0-0686-41d2-910a-a3d21928ab94"
				}
			)

		frappe.sendmail(
			recipients=self.email,
			subject=subject,
			template="verify_account",
			args=args,
			now=True,
		)
