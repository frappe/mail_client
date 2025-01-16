// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("DMARC Report", {
	refresh(frm) {
		frm.trigger("add_actions");
	},

	add_actions(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("DMARC Viewer"), () => {
				frappe.route_options = {
					name: frm.doc.name,
					show_local_ips_only: 0,
				};
				frappe.set_route("query-report", "DMARC Report Viewer");
			});
		}
	},
});
