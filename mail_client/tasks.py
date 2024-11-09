import frappe

from mail_client.mail_client.doctype.incoming_mail.incoming_mail import fetch_emails_from_mail_server
from mail_client.mail_client.doctype.outgoing_mail.outgoing_mail import (
	fetch_and_update_delivery_statuses,
	transfer_emails_to_mail_server,
)
from mail_client.utils import enqueue_job


def enqueue_transfer_emails_to_mail_server() -> None:
	"Called by the scheduler to enqueue the `transfer_emails_to_mail_server` job."

	frappe.session.user = "Administrator"
	enqueue_job(transfer_emails_to_mail_server, queue="long")


@frappe.whitelist()
def enqueue_fetch_and_update_delivery_statuses() -> None:
	"Called by the scheduler to enqueue the `fetch_and_update_delivery_statuses` job."

	frappe.session.user = "Administrator"
	enqueue_job(fetch_and_update_delivery_statuses, queue="long")


@frappe.whitelist()
def enqueue_fetch_emails_from_mail_server() -> None:
	"Called by the scheduler to enqueue the `fetch_emails_from_mail_server` job."

	frappe.session.user = "Administrator"
	enqueue_job(fetch_emails_from_mail_server, queue="long")
