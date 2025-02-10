// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.listview_settings['DNS Record'] = {
	refresh: (listview) => {
		listview.page.add_inner_button('Verify All', () => {
			verify_all_dns_records(listview)
		})
	},
}

function verify_all_dns_records(listview) {
	frappe.call({
		method: 'mail.tasks.enqueue_verify_all_dns_records',
		freeze: true,
		freeze_message: __('Creating Job...'),
		callback: () => {
			frappe.show_alert({
				message: __('{0} job has been created.', [__('Verify DNS Records').bold()]),
				indicator: 'green',
			})
		},
	})
}
