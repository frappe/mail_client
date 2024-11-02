// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mailbox", {
	setup(frm) {
        frm.trigger("set_queries");
    },

    refresh(frm) {
        frm.trigger("add_actions");
	},

	set_queries(frm) {
		frm.set_query("domain_name", () => ({
            filters: {
                "enabled": 1,
                "is_verified": 1,
            }
        }));

		frm.set_query("user", () => ({
            query: "mail.utils.query.get_users_with_mailbox_user_role",
            filters: {
				enabled: 1,
				role: "Mailbox User",
			},
        }));
    },

    add_actions(frm) {
        if (frm.doc.__islocal || !has_common(frappe.user_roles, ["Administrator", "System Manager"])) return;

        frm.add_custom_button(__("Delete Incoming Mails"), () => {
            frappe.confirm(
                __("Are you certain you wish to proceed?"),
                () => frm.trigger("delete_incoming_mails")
            )
        }, __("Actions"));

        frm.add_custom_button(__("Delete Outgoing Mails"), () => {
            frappe.confirm(
                __("Are you certain you wish to proceed?"),
                () => frm.trigger("delete_outgoing_mails")
            )
        }, __("Actions"));
    },

    delete_incoming_mails(frm) {
        frappe.call({
			method: "mail.mail.doctype.mailbox.mailbox.delete_incoming_mails",
			args: {
				mailbox: frm.doc.name,
			},
			freeze: true,
			freeze_message: __("Deleting Incoming Mails..."),
		});
    },

    delete_outgoing_mails(frm) {
        frappe.call({
			method: "mail.mail.doctype.mailbox.mailbox.delete_outgoing_mails",
			args: {
				mailbox: frm.doc.name,
			},
			freeze: true,
			freeze_message: __("Deleting Outgoing Mails..."),
		});
    },
});
