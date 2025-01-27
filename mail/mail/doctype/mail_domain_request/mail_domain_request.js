// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mail Domain Request", {
	refresh(frm) {
		frm.trigger("add_actions");
	},

	add_actions(frm) {
		if (frm.doc.__islocal) return;

		frm.add_custom_button(__("Verify DNS Record"), () => {
			frm.call("verify_key");
		});
	},
});
