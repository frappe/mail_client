import frappe


def get_context(context):
	context.no_cache = 1
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	context = frappe._dict()
	context.csrf_token = csrf_token
	return context
