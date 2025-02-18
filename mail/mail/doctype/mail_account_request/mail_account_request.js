// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Mail Account Request', {
	refresh(frm) {
		frm.trigger('add_actions')
		frm.trigger('set_is_invite')
		frm.trigger('set_invited_by')
		frm.trigger('set_tenant')
		frm.trigger('make_fields_read_only')
	},

	is_invite(frm) {
		frm.trigger('set_is_admin')
	},

	tenant(frm) {
		frm.trigger('set_domain_query')
	},

	add_actions(frm) {
		if (frm.doc.__islocal || frm.doc.is_verified) return

		frm.add_custom_button(
			__('Send Verification Email'),
			() => {
				frm.trigger('send_verification_email')
			},
			__('Actions'),
		)

		if (!frm.doc.is_invite) return

		frm.add_custom_button(
			__('Force Verify and Create Account'),
			() => {
				frm.trigger('force_verify_and_create_account')
			},
			__('Actions'),
		)
	},

	set_is_admin(frm) {
		if (!frm.doc.is_invite) {
			frm.set_value('is_admin', 1)
		}
	},

	set_is_invite(frm) {
		if (frm.doc.__islocal && !frm.doc.is_invite) {
			frm.set_value('is_invite', 1)
		}
	},

	set_invited_by(frm) {
		if (frm.doc.__islocal && !frm.doc.invited_by) {
			frm.set_value('invited_by', frappe.session.user)
		}
	},

	set_tenant(frm) {
		if (frm.doc.__islocal && !frm.doc.tenant) {
			frappe.call({
				method: 'mail.utils.user.get_user_tenant',
				callback: (r) => {
					if (r.message) {
						frm.set_value('tenant', r.message)
					}
				},
			})
		}
	},

	set_domain_query(frm) {
		frm.set_query('domain_name', () => ({
			filters: {
				tenant: frm.doc.tenant,
				is_verified: 1,
			},
		}))
	},

	make_fields_read_only(frm) {
		if (frappe.user_roles.includes('System Manager')) return

		frm.set_df_property('is_invite', 'read_only', 1)
		frm.set_df_property('invited_by', 'read_only', 1)
		frm.set_df_property('tenant', 'read_only', 1)
	},

	send_verification_email(frm) {
		frm.call('send_verification_email')
	},

	force_verify_and_create_account(frm) {
		const dialog = new frappe.ui.Dialog({
			title: 'User Details',
			fields: [
				{
					label: __('First Name'),
					fieldname: 'first_name',
					fieldtype: 'Data',
					reqd: 1,
				},
				{
					label: __('Last Name'),
					fieldname: 'last_name',
					fieldtype: 'Data',
				},
				{
					label: __('Password'),
					fieldname: 'password',
					fieldtype: 'Password',
					reqd: 1,
				},
			],
			size: 'small',
			primary_action_label: 'Create Account',
			primary_action(values) {
				frm.call({
					doc: frm.doc,
					method: 'force_verify_and_create_account',
					args: {
						first_name: values.first_name,
						last_name: values.last_name,
						password: values.password,
					},
					freeze: true,
					freeze_message: __('Creating Account...'),
					callback: (r) => {
						if (!r.exc) {
							frm.refresh()
						}
					},
				})
				dialog.hide()
			},
		})

		dialog.show()
	},
})
