# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
import frappe
from frappe import _
from frappe.utils import flt
from datetime import datetime
from frappe.query_builder import Order, Criterion
from frappe.query_builder.functions import Date, IfNull
from mail.utils.user import has_role, is_system_manager, get_user_mailboxes


def execute(filters: dict | None = None) -> tuple:
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	summary = get_summary(data)

	return columns, data, None, chart, summary


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
			"label": _("Creation"),
			"fieldname": "creation",
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
			"label": _("Response Message"),
			"fieldname": "response",
			"fieldtype": "Code",
			"width": 500,
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
			"label": _("Subject"),
			"fieldname": "subject",
			"fieldtype": "Code",
			"width": 500,
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
			OM.creation,
			MR.status,
			MR.retries,
			OM.message_size,
			OM.via_api,
			OM.is_newsletter,
			MR.response,
			OM.domain_name,
			OM.ip_address,
			OM.sender,
			MR.email.as_("recipient"),
			OM.subject,
			OM.message_id,
		)
		.where((OM.docstatus == 1) & (IfNull(MR.status, "") != ""))
		.orderby(OM.creation, OM.created_at, order=Order.desc)
		.orderby(MR.idx, order=Order.asc)
	)

	if not filters.get("name") and not filters.get("message_id"):
		query = query.where(
			(Date(OM.created_at) >= Date(filters.get("from_date")))
			& (Date(OM.created_at) <= Date(filters.get("to_date")))
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

	data = query.run(as_dict=True)

	for row in data:
		response = json.loads(row["response"])
		row["response"] = (
			response.get("dsn_msg")
			or response.get("reason")
			or response.get("dsn_smtp_response")
			or response.get("response")
		)

	return data


def get_chart(data: list) -> list[dict]:
	labels, sent, deffered, bounced = [], [], [], []

	for row in reversed(data):
		if not isinstance(row["creation"], datetime):
			frappe.throw(_("Invalid date format"))

		date = row["creation"].date().strftime("%d-%m-%Y")

		if date not in labels:
			labels.append(date)

			if row["status"] == "Sent":
				sent.append(1)
				deffered.append(0)
				bounced.append(0)
			elif row["status"] == "Deferred":
				sent.append(0)
				deffered.append(1)
				bounced.append(0)
			elif row["status"] == "Bounced":
				sent.append(0)
				deffered.append(0)
				bounced.append(1)
			else:
				sent.append(0)
				deffered.append(0)
				bounced.append(0)
		else:
			idx = labels.index(date)
			if row["status"] == "Sent":
				sent[idx] += 1
			elif row["status"] == "Deferred":
				deffered[idx] += 1
			elif row["status"] == "Bounced":
				bounced[idx] += 1

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "bounced", "values": bounced},
				{"name": "deffered", "values": deffered},
				{"name": "sent", "values": sent},
			],
		},
		"fieldtype": "Int",
		"type": "bar",
		"axisOptions": {"xIsSeries": -1},
	}


def get_summary(data: list) -> list[dict]:
	if not data:
		return []

	status_count = {}

	for row in data:
		status = row["status"]
		if status in ["Sent", "Deferred", "Bounced"]:
			status_count.setdefault(status, 0)
			status_count[status] += 1

	return [
		{
			"label": _("Sent"),
			"datatype": "Int",
			"value": status_count.get("Sent", 0),
			"indicator": "green",
		},
		{
			"label": _("Deferred"),
			"datatype": "Int",
			"value": status_count.get("Deferred", 0),
			"indicator": "blue",
		},
		{
			"label": _("Bounced"),
			"datatype": "Int",
			"value": status_count.get("Bounced", 0),
			"indicator": "red",
		},
	]
