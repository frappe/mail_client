// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mail Domain", {
	refresh(frm) {
		frm.trigger("add_actions");
	},

	add_actions(frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(
				__("Mail Tracker"),
				() => {
					frappe.route_options = {
						domain_name: frm.doc.name,
					};
					frappe.set_route("query-report", "Mail Tracker");
				},
				__("Reports")
			);

			frm.add_custom_button(
				__("Outbound Delay"),
				() => {
					frappe.route_options = {
						domain_name: frm.doc.name,
					};
					frappe.set_route("query-report", "Outbound Delay");
				},
				__("Reports")
			);

			frm.add_custom_button(
				__("Outgoing Mail Summary"),
				() => {
					frappe.route_options = {
						domain_name: frm.doc.name,
					};
					frappe.set_route("query-report", "Outgoing Mail Summary");
				},
				__("Reports")
			);

			frm.add_custom_button(
				__("Verify DNS Records"),
				() => {
					frm.trigger("verify_dns_records");
				},
				__("Actions")
			);

			frm.add_custom_button(
				__("Refresh DNS Records"),
				() => {
					frappe.confirm(
						__(
							"Are you sure you want to refresh the DNS records? If there are any changes, you'll need to update the DNS settings with your DNS provider accordingly."
						),
						() => frm.trigger("refresh_dns_records")
					);
				},
				__("Actions")
			);

			frm.add_custom_button(
				__("Rotate DKIM Keys"),
				() => {
					frappe.confirm(
						__(
							"Are you sure you want to rotate the DKIM keys? This will generate new keys for email signing and may take up to 10 minutes to propagate across DNS servers. Emails sent during this period may fail DKIM verification."
						),
						() => frm.trigger("rotate_dkim_keys")
					);
				},
				__("Actions")
			);
		}
	},

	verify_dns_records(frm) {
		frappe.call({
			doc: frm.doc,
			method: "verify_dns_records",
			args: {},
			freeze: true,
			freeze_message: __("Verifying DNS Records..."),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh();
				}
			},
		});
	},

	refresh_dns_records(frm) {
		frappe.call({
			doc: frm.doc,
			method: "refresh_dns_records",
			args: {},
			freeze: true,
			freeze_message: __("Refreshing DNS Records..."),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh();
				}
			},
		});
	},

	rotate_dkim_keys(frm) {
		frappe.call({
			doc: frm.doc,
			method: "rotate_dkim_keys",
			args: {},
			freeze: true,
			freeze_message: __("Rotating DKIM Keys..."),
			callback: (r) => {
				if (!r.exc) {
					frm.refresh();
				}
			},
		});
	},
});
