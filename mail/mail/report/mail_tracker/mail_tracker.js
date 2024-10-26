// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Mail Tracker"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
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
			fieldtype: "Select",
			options: ["", "Pending", "Failed", "Queued", "Blocked", "Deferred", "Bounced", "Partially Sent", "Sent"],
		},
		{
			fieldname: "domain_name",
			label: __("Domain Name"),
			fieldtype: "Link",
			options: "Mail Domain",
		},
		{
			fieldname: "sender",
			label: __("Sender"),
			fieldtype: "Link",
			options: "Mailbox",
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
	]
};
