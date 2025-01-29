// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.listview_settings["Mail Agent Request Log"] = {
	get_indicator: (doc) => {
		const status_colors = {
			Queued: "blue",
			Running: "yellow",
			Completed: "green",
			Failed: "red",
		};
		return [__(doc.status), status_colors[doc.status], "status,=," + doc.status];
	},
};
