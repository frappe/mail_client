// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mail Agent Job", {
	setup(frm) {
		frm.trigger("set_queries");
	},

	set_queries(frm) {
		frm.set_query("agent", () => ({
			filters: {
				enabled: 1,
			},
		}));
	},
});
