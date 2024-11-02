// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Incoming Mail", {
	refresh(frm) {
        frm.trigger("add_actions");
	},

    add_actions(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Reply"), () => {
                frm.trigger("reply");
            }, __("Actions"));
            frm.add_custom_button(__("Reply All"), () => {
                frm.trigger("reply_all");
            }, __("Actions"));
        }
    },

    reply(frm) {
        frappe.model.open_mapped_doc({
			method: "mail.mail.doctype.incoming_mail.incoming_mail.reply_to_mail",
			frm: frm,
            args: {
                all: false,
            },
		});
    },

    reply_all(frm) {
        frappe.model.open_mapped_doc({
			method: "mail.mail.doctype.incoming_mail.incoming_mail.reply_to_mail",
			frm: frm,
            args: {
                all: true,
            },
		});
    }
});
