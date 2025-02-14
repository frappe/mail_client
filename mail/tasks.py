import frappe

from mail.mail.doctype.dns_record.dns_record import verify_all_dns_records
from mail.mail.doctype.incoming_mail.incoming_mail import fetch_emails_from_mail_agents
from mail.mail.doctype.outgoing_mail.outgoing_mail import (
	delete_newsletters,
	transfer_emails_to_agent,
	transfer_failed_emails_to_agent,
)
from mail.utils import enqueue_job


@frappe.whitelist()
def enqueue_transfer_emails_to_agent() -> None:
	"Called by the scheduler to enqueue the `transfer_emails_to_agent` job."

	frappe.session.user = "Administrator"
	enqueue_job(transfer_emails_to_agent, queue="long")


@frappe.whitelist()
def enqueue_transfer_failed_emails_to_agent() -> None:
	"Called by the scheduler to enqueue the `transfer_failed_emails_to_agent` job."

	frappe.session.user = "Administrator"
	enqueue_job(transfer_failed_emails_to_agent, queue="long")


@frappe.whitelist()
def enqueue_delete_newsletters() -> None:
	"Called by the scheduler to enqueue the `delete_newsletters` job."

	frappe.session.user = "Administrator"
	enqueue_job(delete_newsletters, queue="long")


@frappe.whitelist()
def enqueue_fetch_emails_from_mail_agents() -> None:
	"Called by the scheduler to enqueue the `fetch_emails_from_mail_agents` job."

	frappe.session.user = "Administrator"
	enqueue_job(fetch_emails_from_mail_agents, queue="long")


@frappe.whitelist()
def enqueue_verify_all_dns_records() -> None:
	"Called by the scheduler to enqueue the `verify_all_dns_records` job."

	enqueue_job(verify_all_dns_records, queue="long")
