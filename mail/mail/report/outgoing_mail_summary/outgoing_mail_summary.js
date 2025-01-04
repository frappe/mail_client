// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Outgoing Mail Summary"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
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
				return ["", "Blocked", "Deferred", "Bounced", "Sent"];
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
			fieldname: "agent",
			label: __("Agent"),
			fieldtype: "MultiSelectList",
			get_data: (txt) => {
				return frappe.db.get_link_options("Mail Agent", txt, {
					enabled: 1,
					enable_outbound: 1,
				});
			},
		},
		{
			fieldname: "priority",
			label: __("Priority"),
			fieldtype: "Int",
		},
		{
			fieldname: "ip_address",
			label: __("IP Address"),
			fieldtype: "Data",
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
			fieldname: "email",
			label: __("Recipient"),
			fieldtype: "Data",
			options: "Email",
		},
		{
			fieldname: "subject",
			label: __("Subject"),
			fieldtype: "Data",
		},
		{
			fieldname: "message_id",
			label: __("Message ID"),
			fieldtype: "Data",
		},
		{
			fieldname: "include_newsletter",
			label: __("Include Newsletter"),
			fieldtype: "Check",
			default: 0,
		},
	],
};
