// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Outgoing Mail', {
	refresh(frm) {
		frm.trigger('hide_amend_button')
		frm.trigger('add_actions')
		frm.trigger('add_comments')
		frm.trigger('set_from_')
	},

	hide_amend_button(frm) {
		if (frm.doc.docstatus == 2) {
			frm.page.btn_primary.hide()
		}
	},

	add_actions(frm) {
		if (frm.doc.docstatus !== 1) return

		if (['Pending', 'Blocked'].includes(frm.doc.status)) {
			if (!frappe.user_roles.includes('System Manager')) return

			frm.add_custom_button(
				__('Force Accept'),
				() => {
					frm.trigger('force_accept')
				},
				__('Actions'),
			)
		} else if (frm.doc.status === 'Accepted') {
			frm.add_custom_button(
				__('Transfer to Agent'),
				() => {
					frm.trigger('transfer_to_mail_agent')
				},
				__('Actions'),
			)
		} else if (frm.doc.status === 'Failed' && frm.doc.failed_count < 5) {
			frm.add_custom_button(
				__('Retry'),
				() => {
					frm.trigger('retry_failed')
				},
				__('Actions'),
			)
		} else if (frm.doc.status === 'Transferring') {
			if (!frappe.user_roles.includes('System Manager')) return

			frm.add_custom_button(
				__('Force Transfer to Agent'),
				() => {
					frappe.confirm(
						__(
							'Are you sure you want to force transfer this email to the agent? It may cause duplicate emails to be sent.',
						),
						() => frm.trigger('force_transfer_to_mail_agent'),
					)
				},
				__('Actions'),
			)
		} else if (frm.doc.status === 'Sent') {
			frm.add_custom_button(
				__('Reply'),
				() => {
					frm.trigger('reply')
				},
				__('Actions'),
			)
			frm.add_custom_button(
				__('Reply All'),
				() => {
					frm.trigger('reply_all')
				},
				__('Actions'),
			)
		} else if (frm.doc.status === 'Bounced') {
			if (!frappe.user_roles.includes('System Manager')) return

			frm.add_custom_button(
				__('Retry'),
				() => {
					frm.trigger('retry_bounced')
				},
				__('Actions'),
			)
		}
	},

	add_comments(frm) {
		if (!frm.doc.__islocal && frm.doc.status == 'Blocked' && frm.doc.error_message) {
			frm.dashboard.add_comment(__(frm.doc.error_message), 'red', true)
		}
	},

	set_from_(frm) {
		if (!frm.doc.from_) {
			frappe.call({
				method: 'mail.mail.doctype.outgoing_mail.outgoing_mail.get_from_',
				callback: (r) => {
					if (r.message) {
						frm.set_value('from_', r.message)
					}
				},
			})
		}
	},

	force_accept(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'force_accept',
			freeze: true,
			freeze_message: __('Force Accepting...'),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh()
				}
			},
		})
	},

	retry_failed(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'retry_failed',
			freeze: true,
			freeze_message: __('Retrying...'),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh()
				}
			},
		})
	},

	transfer_to_mail_agent(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'transfer_to_mail_agent',
			freeze: true,
			freeze_message: __('Transferring...'),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh()
				}
			},
		})
	},

	force_transfer_to_mail_agent(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'force_transfer_to_mail_agent',
			freeze: true,
			freeze_message: __('Force Transferring...'),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh()
				}
			},
		})
	},

	reply(frm) {
		frappe.model.open_mapped_doc({
			method: 'mail.mail.doctype.outgoing_mail.outgoing_mail.reply_to_mail',
			frm: frm,
			args: {
				all: false,
			},
		})
	},

	reply_all(frm) {
		frappe.model.open_mapped_doc({
			method: 'mail.mail.doctype.outgoing_mail.outgoing_mail.reply_to_mail',
			frm: frm,
			args: {
				all: true,
			},
		})
	},

	retry_bounced(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'retry_bounced',
			freeze: true,
			freeze_message: __('Retrying...'),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh()
				}
			},
		})
	},
})

frappe.ui.form.on('Mail Recipient', {
	check_deliverability(frm, cdt, cdn) {
		const recipient = locals[cdt][cdn]
		const email = recipient.email

		if (!email) return

		frappe.call({
			method: 'mail.utils.check_deliverability',
			args: {
				email: email,
			},
			freeze: true,
			freeze_message: __('Checking email deliverability...'),
			callback: (r) => {
				if (!r.exc) {
					if (r.message) {
						frappe.show_alert({
							message: __('The email address {0} is deliverable.', [email.bold()]),
							indicator: 'green',
						})
					} else {
						frappe.show_alert({
							message: __('The email address {0} appears to be invalid.', [
								email.bold(),
							]),
							indicator: 'red',
						})
					}
				}
			},
		})
	},
})
