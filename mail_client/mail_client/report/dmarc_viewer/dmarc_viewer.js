// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["DMARC Viewer"] = {
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (["spf_result", "dkim_result", "result"].includes(column.fieldname)) {
			if (data[column.fieldname] == "PASS") {
				value = "<span style='color:green'>" + value + "</span>";
			} else {
				value = "<span style='color:red'>" + value + "</span>";
			}
		}

		return value;
	},

	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -7),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "name",
			label: __("DMARC Report"),
			fieldtype: "Link",
			options: "DMARC Report",
		},
		{
			fieldname: "domain_name",
			label: __("Domain Name"),
			fieldtype: "Link",
			options: "Mail Domain",
		},
		{
			fieldname: "organization",
			label: __("Organization"),
			fieldtype: "Data",
		},
		{
			fieldname: "report_id",
			label: __("Report ID"),
			fieldtype: "Data",
		},
	],
};
