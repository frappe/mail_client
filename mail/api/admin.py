import frappe

from mail.utils.dns import verify_dns_record


@frappe.whitelist()
def create_tenant(tenant_name):
	tenant = frappe.new_doc("Mail Tenant")
	tenant.tenant_name = tenant_name
	tenant.user = frappe.session.user
	tenant.append("tenant_members", {"user": frappe.session.user})
	tenant.insert()


@frappe.whitelist()
def create_domain_request(domain_name, mail_tenant):
	domain_request = frappe.new_doc("Mail Domain Request")
	domain_request.domain_name = domain_name
	domain_request.mail_tenant = mail_tenant
	domain_request.user = frappe.session.user
	domain_request.insert()
	return domain_request


@frappe.whitelist()
def verify_domain_key(domain_request):
	doc = frappe.get_doc("Mail Domain Request", domain_request)
	return doc.verify_key()
