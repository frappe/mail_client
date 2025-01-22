// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["DMARC Report Viewer"] = {
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (["spf_result", "dkim_result", "result"].includes(column.fieldname)) {
			value =
				data[column.fieldname] === "PASS"
					? `<span style='color:green'>${value}</span>`
					: `<span style='color:red'>${value}</span>`;
		} else if (column.fieldname === "source_ip" && data[column.fieldname]) {
			value = data["is_local_ip"]
				? `<span style='color:green'>${value}</span>`
				: `<span style='color:black'>${value}</span>`;
		}

		return value;
	},

	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.get_today(), -1),
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
			fieldtype: "MultiSelectList",
			get_data: (txt) => {
				return frappe.db.get_link_options("Mail Domain", txt);
			},
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
		{
			fieldname: "source_ip",
			label: __("Source IP"),
			fieldtype: "Data",
		},
		{
			fieldname: "disposition",
			label: __("Disposition"),
			fieldtype: "Select",
			options: ["", "none", "quarantine", "reject"],
		},
		{
			fieldname: "header_from",
			label: __("Header From"),
			fieldtype: "Data",
		},
		{
			fieldname: "envelope_from",
			label: __("Envelope From"),
			fieldtype: "Data",
		},
		{
			fieldname: "spf_result",
			label: __("SPF Result"),
			fieldtype: "Select",
			options: ["", "PASS", "FAIL"],
		},
		{
			fieldname: "dkim_result",
			label: __("DKIM Result"),
			fieldtype: "Select",
			options: ["", "PASS", "FAIL"],
		},
		{
			fieldname: "show_local_ips_only",
			label: __("Show Local IPs Only"),
			fieldtype: "Check",
			default: 1,
		},
	],
};
