// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bounce Log', {
	check_deliverability(frm) {
		const email = frm.doc.email

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
