// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.listview_settings['Incoming Mail'] = {
	refresh: (listview) => {
		listview.page.add_inner_button('Fetch Emails', () => {
			fetch_emails_from_mail_agents(listview)
		})
	},

	get_indicator: (doc) => {
		const status_colors = {
			Draft: 'grey',
			Submitted: 'blue',
			Cancelled: 'red',
		}
		return [__(doc.status), status_colors[doc.status], 'status,=,' + doc.status]
	},
}

function fetch_emails_from_mail_agents() {
	frappe.call({
		method: 'mail.tasks.enqueue_fetch_emails_from_mail_agents',
		freeze: true,
		freeze_message: __('Creating Job...'),
		callback: () => {
			frappe.show_alert({
				message: __('{0} job has been created.', [__('Fetch Emails').bold()]),
				indicator: 'green',
			})
		},
	})
}
