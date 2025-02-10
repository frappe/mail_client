// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Mail Settings', {
	refresh(frm) {
		frm.trigger('add_comments')
	},

	add_comments(frm) {
		if (frm.doc.root_domain_name && (!frm.doc.dns_provider || !frm.doc.dns_provider_token)) {
			const bold_root_domain_name = `<b>${frm.doc.root_domain_name}</b>`
			const dns_record_list_link = `<a href="/app/dns-record">${__('DNS Records')}</a>`
			const msg = __(
				'DNS provider or token not configured. Please manually add the {0} to the DNS provider for the domain {1} to ensure proper email authentication.',
				[dns_record_list_link, bold_root_domain_name],
			)
			frm.dashboard.add_comment(msg, 'yellow', true)
		}
	},
})
