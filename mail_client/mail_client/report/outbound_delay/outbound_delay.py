# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.query_builder import Criterion, Order
from frappe.query_builder.functions import Date, IfNull
from frappe.utils import flt

from mail_client.utils.user import get_user_mailboxes, has_role, is_system_manager


def execute(filters: dict | None = None) -> tuple[list, list]:
	columns = get_columns()
	data = get_data(filters)
	summary = get_summary(data)

	return columns, data, None, None, summary


def get_columns() -> list[dict]:
	return [
		{
			"label": _("Name"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Outgoing Mail",
			"width": 100,
		},
		{
			"label": _("Submitted At"),
			"fieldname": "submitted_at",
			"fieldtype": "Datetime",
			"width": 180,
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": _("Retries"),
			"fieldname": "retries",
			"fieldtype": "Int",
			"width": 80,
		},
		{
			"label": _("Message Size"),
			"fieldname": "message_size",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("API"),
			"fieldname": "via_api",
			"fieldtype": "Check",
			"width": 60,
		},
		{
			"label": _("Newsletter"),
			"fieldname": "is_newsletter",
			"fieldtype": "Check",
			"width": 100,
		},
		{
			"label": _("Submission Delay"),
			"fieldname": "submission_delay",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Transfer Delay"),
			"fieldname": "transfer_delay",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Action Delay"),
			"fieldname": "action_delay",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Total Delay"),
			"fieldname": "total_delay",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Domain Name"),
			"fieldname": "domain_name",
			"fieldtype": "Link",
			"options": "Mail Domain",
			"width": 150,
		},
		{
			"label": _("IP Address"),
			"fieldname": "ip_address",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("Sender"),
			"fieldname": "sender",
			"fieldtype": "Link",
			"options": "Mailbox",
			"width": 200,
		},
		{
			"label": _("Recipient"),
			"fieldname": "recipient",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Message ID"),
			"fieldname": "message_id",
			"fieldtype": "Data",
			"width": 200,
		},
	]


def get_data(filters: dict | None = None) -> list[list]:
	filters = filters or {}

	OM = frappe.qb.DocType("Outgoing Mail")
	MR = frappe.qb.DocType("Mail Recipient")

	query = (
		frappe.qb.from_(OM)
		.left_join(MR)
		.on(OM.name == MR.parent)
		.select(
			OM.name,
			OM.submitted_at,
			MR.status,
			MR.retries,
			OM.message_size,
			OM.via_api,
			OM.is_newsletter,
			OM.submitted_after.as_("submission_delay"),
			(OM.transfer_started_after + OM.transfer_completed_after).as_("transfer_delay"),
			MR.action_after.as_("action_delay"),
			(
				OM.submitted_after + OM.transfer_started_after + OM.transfer_completed_after + MR.action_after
			).as_("total_delay"),
			OM.domain_name,
			OM.ip_address,
			OM.sender,
			MR.email.as_("recipient"),
			OM.message_id,
		)
		.where((OM.docstatus == 1) & (IfNull(MR.status, "") != ""))
		.orderby(OM.submitted_at, order=Order.desc)
		.orderby(MR.idx, order=Order.asc)
	)

	if not filters.get("name") and not filters.get("message_id"):
		query = query.where(
			(Date(OM.submitted_at) >= Date(filters.get("from_date")))
			& (Date(OM.submitted_at) <= Date(filters.get("to_date")))
		)

	if not filters.get("include_newsletter"):
		query = query.where(OM.is_newsletter == 0)

	for field in [
		"name",
		"domain_name",
		"ip_address",
		"sender",
		"message_id",
	]:
		if filters.get(field):
			query = query.where(OM[field] == filters.get(field))

	for field in ["status", "email"]:
		if filters.get(field):
			query = query.where(MR[field] == filters.get(field))

	user = frappe.session.user
	if not is_system_manager(user):
		conditions = []
		mailboxes = get_user_mailboxes(user)

		if has_role(user, "Mailbox User") and mailboxes:
			conditions.append(OM.sender.isin(mailboxes))

		if not conditions:
			return []

		query = query.where(Criterion.any(conditions))

	return query.run(as_dict=True)


def get_summary(data: list) -> list[dict]:
	if not data:
		return []

	summary_data = {}
	average_data = {}

	for row in data:
		for field in ["message_size", "submission_delay", "transfer_delay", "action_delay"]:
			key = f"total_{field}"
			summary_data.setdefault(key, 0)
			summary_data[key] += row[field]

	for key, value in summary_data.items():
		key = key.replace("total_", "")
		average_data[key] = flt(value / len(data) if data else 0, 1)

	return [
		{
			"label": _("Average Message Size"),
			"datatype": "Int",
			"value": average_data["message_size"],
			"indicator": "green",
		},
		{
			"label": _("Average Submission Delay"),
			"datatype": "Data",
			"value": f"{average_data['submission_delay']}s",
			"indicator": "yellow",
		},
		{
			"label": _("Average Transfer Delay"),
			"datatype": "Data",
			"value": f"{average_data['transfer_delay']}s",
			"indicator": "blue",
		},
		{
			"label": _("Average Action Delay"),
			"datatype": "Data",
			"value": f"{average_data['action_delay']}s",
			"indicator": "orange",
		},
	]
