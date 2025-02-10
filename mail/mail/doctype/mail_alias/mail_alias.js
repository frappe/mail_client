// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Mail Alias', {
	setup(frm) {
		frm.trigger('set_queries')
	},

	set_queries(frm) {
		frm.set_query('alias_for_name', () => ({
			filters: {
				enabled: 1,
			},
		}))

		frm.set_query('domain_name', () => ({
			filters: {
				enabled: 1,
				is_verified: 1,
			},
		}))
	},
})
