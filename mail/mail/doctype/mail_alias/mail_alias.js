// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mail Alias", {
	setup(frm) {
        frm.trigger("set_queries");
    },

    set_queries(frm) {
		frm.set_query("domain_name", () => ({
            filters: {
                "enabled": 1,
                "is_verified": 1,
            }
        }));

        frm.set_query("mailbox", "mailboxes", (doc) => {
			let filters = {
				"domain_name": doc.domain_name || " ",
				"incoming": 1,
			};

			let selected_mailboxes = frm.doc.mailboxes.map((d) => d.mailbox);
			if (selected_mailboxes.length) {
				filters.name = ["not in", selected_mailboxes];
			}

			return {
				filters: filters,
			};
		});
    },
});


