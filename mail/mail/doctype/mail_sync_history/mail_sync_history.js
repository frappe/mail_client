// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mail Sync History", {
	setup(frm) {
		frm.trigger("set_queries");
	},

	set_queries(frm) {
		frm.set_query("user", () => ({
			filters: {
				enabled: 1,
			},
		}));

		frm.set_query("account", () => ({
			filters: {
				enabled: 1,
			},
		}));
	},
});
