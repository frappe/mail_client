import json

import frappe
from frappe import _
from frappe.utils import convert_utc_to_system_timezone, get_datetime

from mail.mail.doctype.incoming_mail.incoming_mail import process_incoming_mail


@frappe.whitelist(methods=["POST"], allow_guest=True)
def update_delivery_status() -> None:
	"""Update Delivery Status."""

	try:
		data = json.loads(frappe.request.data.decode())
		doc = frappe.get_doc("Outgoing Mail", data["outgoing_mail"])
		doc._update_delivery_status(data, notify_update=True)
	except Exception:
		error_log = frappe.get_traceback(with_context=False)
		frappe.log_error(title=f"Update Delivery Status - {data['outgoing_mail']}", message=error_log)


@frappe.whitelist(methods=["POST"], allow_guest=True)
def receive_email() -> None:
	"""Receive Email."""

	try:
		data = json.loads(frappe.request.data.decode())
		mail_domain = frappe.get_cached_doc("Mail Domain", data["domain_name"])

		if not mail_domain.enabled:
			frappe.throw(_("Mail Domain {0} is disabled").format(data["domain_name"]))

		if data["inbound_token"] != mail_domain.get_password("inbound_token"):
			frappe.throw(_("Invalid Inbound Token"))

		process_incoming_mail(
			incoming_mail_log=data["incoming_mail_log"],
			message=data["message"],
			is_spam=data["is_spam"],
		)
		last_synced_at = convert_utc_to_system_timezone(get_datetime(data["processed_at"]))
		frappe.db.set_single_value("Mail Settings", "last_synced_at", last_synced_at, update_modified=False)
	except Exception:
		error_log = frappe.get_traceback(with_context=False)
		frappe.log_error(title=f"Receive Email - {data['domain_name']}", message=error_log)
