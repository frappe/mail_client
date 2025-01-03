// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Mail Tracker"] = {
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
			label: __("Outgoing Mail"),
			fieldtype: "Link",
			options: "Outgoing Mail",
			get_query: () => {
				return {
					query: "mail.utils.query.get_outgoing_mails",
				};
			},
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "MultiSelectList",
			get_data: (txt) => {
				return [
					"",
					"Pending",
					"Failed",
					"Queued",
					"Blocked",
					"Deferred",
					"Bounced",
					"Partially Sent",
					"Sent",
				];
			},
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
			fieldname: "sender",
			label: __("Sender"),
			fieldtype: "MultiSelectList",
			get_data: (txt) => {
				return frappe.db.get_link_options("Mailbox", txt);
			},
		},
		{
			fieldname: "message_id",
			label: __("Message ID"),
			fieldtype: "Data",
		},
		{
			fieldname: "tracking_id",
			label: __("Tracking ID"),
			fieldtype: "Data",
		},
	],
};
