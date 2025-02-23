# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from datetime import datetime

import frappe
from frappe import _
from frappe.query_builder import Criterion, Order
from frappe.query_builder.functions import Date, IfNull

from mail.utils.cache import get_account_for_user, get_domains_owned_by_tenant, get_tenant_for_user
from mail.utils.user import has_role, is_system_manager


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
			"label": _("Message Size"),
			"fieldname": "message_size",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("Spam Score"),
			"fieldname": "spam_score",
			"fieldtype": "Float",
			"precision": 1,
			"width": 110,
		},
		{
			"label": _("API"),
			"fieldname": "via_api",
			"fieldtype": "Check",
			"width": 60,
		},
		{
			"label": _("Priority"),
			"fieldname": "priority",
			"fieldtype": "Int",
			"width": 80,
		},
		{
			"label": _("Newsletter"),
			"fieldname": "is_newsletter",
			"fieldtype": "Check",
			"width": 100,
		},
		{
			"label": _("Domain Name"),
			"fieldname": "domain_name",
			"fieldtype": "Link",
			"options": "Mail Domain",
			"width": 150,
		},
		{
			"label": _("Agent"),
			"fieldname": "agent",
			"fieldtype": "Link",
			"options": "Mail Agent",
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
			"options": "Mail Account",
			"width": 200,
		},
		{
			"label": _("From"),
			"fieldname": "from_",
			"fieldtype": "Data",
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
			"fieldtype": "Data",
			"width": 500,
		},
		{
			"label": _("Message ID"),
			"fieldname": "message_id",
			"fieldtype": "Data",
			"width": 200,
		},
	]


def get_data(filters: dict | None = None) -> list[dict]:
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
			OM.message_size,
			OM.spam_score,
			OM.via_api,
			OM.priority,
			OM.is_newsletter,
			OM.domain_name,
			OM.agent,
			OM.ip_address,
			OM.sender,
			OM.from_,
			MR.email.as_("recipient"),
			OM.subject,
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

	for field in [
		"name",
		"priority",
		"ip_address",
		"from_",
		"message_id",
	]:
		if filters.get(field):
			query = query.where(OM[field] == filters.get(field))

	for field in [
		"domain_name",
		"sender",
	]:
		if filters.get(field):
			query = query.where(OM[field].isin(filters.get(field)))

	if agent := filters.get("agent"):
		if isinstance(agent, str):
			agent = [agent]
		query = query.where(OM.agent.isin(agent))

	if not filters.get("include_newsletter"):
		query = query.where(OM.is_newsletter == 0)
	if filters.get("subject"):
		query = query.where(OM.subject.like(f"%{filters.get('subject')}%"))

	if filters.get("email"):
		query = query.where(MR["email"] == filters.get("email"))
	if filters.get("status"):
		query = query.where(MR["status"].isin(filters.get("status")))

	user = frappe.session.user
	if not is_system_manager(user):
		conditions = []
		account = get_account_for_user(user)

		if has_role(user, "Mail Admin"):
			if tenant := get_tenant_for_user(user):
				if domains := get_domains_owned_by_tenant(tenant):
					conditions.append(OM.domain_name.isin(domains))
		elif has_role(user, "Mail User") and account:
			conditions.append(OM.sender == account)

		if not conditions:
			return []

		query = query.where(Criterion.any(conditions))

	return query.run(as_dict=True)


def get_chart(data: list) -> list[dict]:
	labels, sent, blocked = [], [], []

	for row in reversed(data):
		if not isinstance(row["submitted_at"], datetime):
			frappe.throw(_("Invalid date format"))

		date = row["submitted_at"].date().strftime("%d-%m-%Y")

		if date not in labels:
			labels.append(date)

			if row["status"] == "Sent":
				sent.append(1)
				blocked.append(0)
			elif row["status"] == "Blocked":
				sent.append(0)
				blocked.append(1)
			else:
				sent.append(0)
				blocked.append(0)
		else:
			idx = labels.index(date)
			if row["status"] == "Sent":
				sent[idx] += 1
			elif row["status"] == "Blocked":
				blocked[idx] += 1

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "blocked", "values": blocked},
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
		if status in ["Sent", "Blocked"]:
			status_count.setdefault(status, 0)
			status_count[status] += 1

	return [
		{
			"label": _("Sent"),
			"datatype": "Int",
			"value": status_count.get("Sent", 0),
			"indicator": "blue",
		},
		{
			"label": _("Blocked"),
			"datatype": "Int",
			"value": status_count.get("Blocked", 0),
			"indicator": "red",
		},
	]
