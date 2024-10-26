// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Outgoing Mail", {
    setup(frm) {
        frm.trigger("set_queries");
    },

	refresh(frm) {
        frm.trigger("hide_amend_button");
        frm.trigger("add_actions");
        frm.trigger("set_sender");
	},

    set_queries(frm) {
        frm.set_query("sender", () => ({
            query: "mail.mail.doctype.outgoing_mail.outgoing_mail.get_sender",
        }));
    },

    hide_amend_button(frm) {
		if (frm.doc.docstatus == 2) {
			frm.page.btn_primary.hide()
		}
	},

    add_actions(frm) {
        if (frm.doc.docstatus === 1) {
            if (frm.doc.status === "Pending") {
                frm.add_custom_button(__("Transfer Now"), () => {
                    frm.trigger("transfer_to_mail_server");
                }, __("Actions"));
            }
            else if (frm.doc.status === "Failed" && frm.doc.failed_count < 3) {
                frm.add_custom_button(__("Retry"), () => {
                    frm.trigger("retry_failed");
                }, __("Actions"));
            }
            else if (["Queued", "Deferred"].includes(frm.doc.status)) {
                frm.add_custom_button(__("Fetch Delivery Status"), () => {
                    frm.trigger("fetch_and_update_delivery_statuses");
                }, __("Actions"));
            }
            else if (frm.doc.status === "Sent") {
                frm.add_custom_button(__("Reply"), () => {
                    frm.trigger("reply");
                }, __("Actions"));
                frm.add_custom_button(__("Reply All"), () => {
                    frm.trigger("reply_all");
                }, __("Actions"));
            }
        }
    },

    set_sender(frm) {
        if (!frm.doc.sender) {
            frappe.call({
                method: "mail.mail.doctype.outgoing_mail.outgoing_mail.get_default_sender",
                callback: (r) => {
                    if (r.message) {
                        frm.set_value("sender", r.message);
                    }
                }
            });
        }
    },

    transfer_to_mail_server(frm) {
        frappe.call({
            doc: frm.doc,
            method: "transfer_to_mail_server",
            freeze: true,
            freeze_message: __("Transferring..."),
            callback: (r) => {
                if (!r.exc) {
                    frm.refresh();
                }
            }
        });
    },

    retry_failed(frm) {
        frappe.call({
            doc: frm.doc,
            method: "retry_failed",
            freeze: true,
            freeze_message: __("Retrying..."),
            callback: (r) => {
                if (!r.exc) {
                    frm.refresh();
                }
            }
        });
    },

    fetch_and_update_delivery_statuses(frm) {
		frappe.call({
			method: "mail.tasks.enqueue_fetch_and_update_delivery_statuses",
			freeze: true,
			freeze_message: __("Creating Job..."),
			callback: () => {
                frappe.show_alert({
                    message: __("{0} job has been created.", [__("Fetch Delivery Statuses").bold()]),
                    indicator: "green",
                });
            }
		});
	},

    reply(frm) {
        frappe.model.open_mapped_doc({
			method: "mail.mail.doctype.outgoing_mail.outgoing_mail.reply_to_mail",
			frm: frm,
            args: {
                all: false,
            },
		});
    },

    reply_all(frm) {
        frappe.model.open_mapped_doc({
			method: "mail.mail.doctype.outgoing_mail.outgoing_mail.reply_to_mail",
			frm: frm,
            args: {
                all: true,
            },
		});
    }
});
