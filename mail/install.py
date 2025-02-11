import frappe

from mail.mail.doctype.rate_limit.rate_limit import create_rate_limit


def after_install() -> None:
	add_rate_limits()
	create_default_tenant()


def add_rate_limits() -> None:
	"""Add rate limits."""

	rate_limits = [
		# mail.api.account
		{"method_path": "mail.api.account.self_signup", "limit": 5, "seconds": 60 * 60},
		{"method_path": "mail.api.account.resend_otp", "limit": 5, "seconds": 60 * 60},
		{"method_path": "mail.api.account.verify_otp", "limit": 5, "seconds": 60 * 60},
		{"method_path": "mail.api.account.get_account_request", "limit": 5, "seconds": 60 * 60},
		{"method_path": "mail.api.account.create_account", "limit": 10, "seconds": 60 * 60},
		# mail.api.admin
		{"method_path": "mail.api.admin.verify_dns_record", "limit": 10, "seconds": 60 * 60},
		{"method_path": "mail.api.admin.add_member", "limit": 10, "seconds": 60 * 60},
		# mail.api.blacklist
		{"method_path": "mail.api.blacklist.get", "limit": 180, "seconds": 60 * 60},
		# mail.api.inbound
		{"method_path": "mail.api.inbound.pull", "limit": 10, "seconds": 60},
		{"method_path": "mail.api.inbound.pull_raw", "limit": 10, "seconds": 60},
		# mail.api.outbound
		{"method_path": "mail.api.outbound.send", "limit": 300, "seconds": 60},
		{"method_path": "mail.api.outbound.send_raw", "limit": 300, "seconds": 60},
		# mail.api.spamd
		{"method_path": "mail.api.spamd.scan", "limit": 60, "seconds": 60},
		{"method_path": "mail.api.spamd.get_spam_score", "limit": 60, "seconds": 60},
		# mail.api.track
		{"method_path": "mail.api.track.open", "limit": 10, "seconds": 60},
	]

	for rl in rate_limits:
		create_rate_limit(**rl)


def create_default_tenant() -> None:
	"""Create the default tenant."""

	tenant = frappe.new_doc("Mail Tenant")
	tenant.tenant_name = "Frappe Mail"
	tenant.user = "Administrator"
	tenant.insert(ignore_permissions=True)
