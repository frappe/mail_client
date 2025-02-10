// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Mail Domain Request', {
	refresh(frm) {
		frm.trigger('add_actions')
		frm.trigger('set_user')
		frm.trigger('set_tenant')
	},

	add_actions(frm) {
		if (frm.doc.__islocal || frm.doc.is_verified) return

		frm.add_custom_button(__('Verify and Create Domain'), () => {
			frm.trigger('verify_and_create_domain')
		})
	},

	set_user(frm) {
		if (frm.doc.__islocal && !frm.doc.user) {
			frm.set_value('user', frappe.session.user)
		}
	},

	set_tenant(frm) {
		if (frm.doc.__islocal && !frm.doc.tenant) {
			frappe.call({
				method: 'mail.utils.user.get_user_tenant',
				callback: (r) => {
					if (r.message) {
						frm.set_value('tenant', r.message)
					}
				},
			})
		}
	},

	verify_and_create_domain(frm) {
		frm.call({
			doc: frm.doc,
			method: 'verify_and_create_domain',
			args: {
				save: true,
			},
			freeze: true,
			freeze_message: __('Creating Domain...'),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh()
				}
			},
		})
	},
})
