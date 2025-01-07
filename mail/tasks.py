import frappe

from mail.mail.doctype.dns_record.dns_record import verify_all_dns_records
from mail.mail.doctype.incoming_mail.incoming_mail import fetch_emails_from_mail_server
from mail.utils import enqueue_job


@frappe.whitelist()
def enqueue_fetch_emails_from_mail_server() -> None:
	"Called by the scheduler to enqueue the `fetch_emails_from_mail_server` job."

	frappe.session.user = "Administrator"
	enqueue_job(fetch_emails_from_mail_server, queue="long")


@frappe.whitelist()
def enqueue_verify_all_dns_records() -> None:
	"Called by the scheduler to enqueue the `verify_all_dns_records` job."

	enqueue_job(verify_all_dns_records, queue="long")
