// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mail Account", {
	setup(frm) {
		frm.trigger("set_queries");
	},

	refresh(frm) {
		frm.trigger("add_actions");
	},

	set_queries(frm) {
		frm.set_query("domain_name", () => ({
			filters: {
				enabled: 1,
				is_verified: 1,
			},
		}));

		frm.set_query("user", () => ({
			query: "mail.utils.query.get_users_with_mail_user_role",
			filters: {
				enabled: 1,
				role: "Mail User",
			},
		}));
	},

	add_actions(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(
				__("Mail Tracker"),
				() => {
					frappe.route_options = {
						sender: frm.doc.name,
					};
					frappe.set_route("query-report", "Mail Tracker");
				},
				__("Reports")
			);

			frm.add_custom_button(
				__("Outbound Delay"),
				() => {
					frappe.route_options = {
						sender: frm.doc.name,
					};
					frappe.set_route("query-report", "Outbound Delay");
				},
				__("Reports")
			);

			frm.add_custom_button(
				__("Outgoing Mail Summary"),
				() => {
					frappe.route_options = {
						sender: frm.doc.name,
					};
					frappe.set_route("query-report", "Outgoing Mail Summary");
				},
				__("Reports")
			);
		}
	},
});
