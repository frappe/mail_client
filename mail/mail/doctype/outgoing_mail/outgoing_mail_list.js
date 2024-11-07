// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.listview_settings["Outgoing Mail"] = {
	get_indicator: (doc) => {
		const status_colors = {
			Draft: "grey",
			Pending: "yellow",
			Queuing: "yellow",
			Failed: "red",
			Queued: "blue",
			Blocked: "red",
			Deferred: "orange",
			Bounced: "pink",
			"Partially Sent": "purple",
			Sent: "green",
			Cancelled: "red",
		};
		return [__(doc.status), status_colors[doc.status], "status,=," + doc.status];
	},
};
