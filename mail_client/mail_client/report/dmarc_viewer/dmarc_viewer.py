# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.query_builder import Order
from frappe.query_builder.functions import Date


def execute(filters: dict | None = None) -> tuple:
	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns() -> list[dict]:
	return [
		{
			"label": _("Name"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "DMARC Report",
			"width": 120,
		},
		{
			"label": _("From Date"),
			"fieldname": "from_date",
			"fieldtype": "Datetime",
			"width": 180,
		},
		{
			"label": _("To Date"),
			"fieldname": "to_date",
			"fieldtype": "Datetime",
			"width": 180,
		},
		{
			"label": _("Domain Name"),
			"fieldname": "domain_name",
			"fieldtype": "Link",
			"options": "Mail Domain",
			"width": 150,
		},
		{
			"label": _("Organization"),
			"fieldname": "organization",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Report ID"),
			"fieldname": "report_id",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Source IP"),
			"fieldname": "source_ip",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Count"),
			"fieldname": "count",
			"fieldtype": "Int",
			"width": 70,
		},
		{
			"label": _("Disposition"),
			"fieldname": "disposition",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Header From"),
			"fieldname": "header_from",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("SPF Result"),
			"fieldname": "spf_result",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("DKIM Result"),
			"fieldname": "dkim_result",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Auth Type"),
			"fieldname": "auth_type",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Selector / Scope"),
			"fieldname": "selector_or_scope",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Domain"),
			"fieldname": "domain",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Result"),
			"fieldname": "result",
			"fieldtype": "Data",
			"width": 150,
		},
	]


def get_data(filters: dict | None = None) -> list[list]:
	filters = filters or {}

	DR = frappe.qb.DocType("DMARC Report")

	query = (
		frappe.qb.from_(DR)
		.select(
			DR.name,
			DR.from_date,
			DR.to_date,
			DR.domain_name,
			DR.organization,
			DR.report_id,
		)
		.orderby(DR.from_date, order=Order.desc)
	)

	if not filters.get("name"):
		query = query.where(
			(Date(DR.from_date) >= Date(filters.get("from_date")))
			& (Date(DR.to_date) <= Date(filters.get("to_date")))
		)

	for field in [
		"name",
		"domain_name",
		"organization",
		"report_id",
	]:
		if filters.get(field):
			query = query.where(DR[field] == filters.get(field))

	data = query.run(as_dict=True)

	formated_data = []
	for d in data:
		records = frappe.db.get_all(
			"DMARC Report Detail",
			filters={"parenttype": "DMARC Report", "parent": d.name},
			fields=[
				"source_ip",
				"count",
				"disposition",
				"header_from",
				"spf_result",
				"dkim_result",
				"auth_results",
			],
		)

		d["indent"] = 0
		formated_data.append(d)
		for record in records:
			record["indent"] = 1
			formated_data.append(record)

			auth_results = json.loads(record.auth_results)
			for auth_result in auth_results:
				auth_result["indent"] = 2

				if auth_result["auth_type"] == "DKIM":
					auth_result["selector_or_scope"] = auth_result.get("selector")
				else:
					auth_result["selector_or_scope"] = auth_result.get("scope")

				formated_data.append(auth_result)

	return formated_data
