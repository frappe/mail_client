import frappe


def after_install() -> None:
	create_default_tenant()


def create_default_tenant() -> None:
	"""Create the default tenant."""

	tenant = frappe.new_doc("Mail Tenant")
	tenant.tenant_name = "Frappe Mail"
	tenant.user = "Administrator"
	tenant.insert(ignore_permissions=True)
