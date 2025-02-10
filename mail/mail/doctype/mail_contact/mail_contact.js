// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Mail Contact', {
	refresh(frm) {
		frm.trigger('set_user')
	},

	set_user(frm) {
		if (frm.doc.__islocal && !frm.doc.user && frappe.session.user) {
			frm.set_value('user', frappe.session.user)
		}
	},
})
