// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('DNS Record', {
	refresh(frm) {
		frm.trigger('add_actions')
		frm.trigger('add_comments')
	},

	add_actions(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(
				__('Verify DNS Record'),
				() => {
					frm.trigger('verify_dns_record')
				},
				__('Actions'),
			)
		}
	},

	add_comments(frm) {
		if (!frm.doc.__islocal && !frm.doc.is_verified) {
			const mail_settings_link = `<a href="/app/mail-settings">${__('Mail Settings')}</a>`
			const msg = __(
				'It seems that the DNS provider or token is not configured in the {0}. Please manually add this DNS record to your provider for the root domain to ensure proper email authentication.',
				[mail_settings_link],
			)
			frm.dashboard.add_comment(msg, 'yellow', true)
		}
	},

	verify_dns_record(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'verify_dns_record',
			args: {
				save: true,
			},
			freeze: true,
			freeze_message: __('Verifying DNS Record...'),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh()
				}
			},
		})
	},
})
