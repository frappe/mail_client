import frappe
from frappe import _


def get_root_domain_name() -> str | None:
	"""Returns the root domain name."""

	def generator() -> str | None:
		return frappe.db.get_single_value("Mail Settings", "root_domain_name")

	return frappe.cache.get_value("root_domain_name", generator)


def get_smtp_limits() -> dict:
	"""Returns the SMTP limits."""

	def generator() -> dict:
		mail_settings = frappe.get_cached_doc("Mail Settings")
		return {
			"max_connections": mail_settings.smtp_max_connections,
			"max_messages": mail_settings.smtp_max_messages,
			"session_duration": mail_settings.smtp_session_duration,
			"inactivity_timeout": mail_settings.smtp_inactivity_timeout,
			"cleanup_interval": mail_settings.smtp_cleanup_interval,
		}

	return frappe.cache.get_value("smtp_limits", generator)


def get_imap_limits() -> dict:
	"""Returns the IMAP limits."""

	def generator() -> dict:
		mail_settings = frappe.get_cached_doc("Mail Settings")
		return {
			"max_connections": mail_settings.imap_max_connections,
			"authenticated_timeout": mail_settings.imap_authenticated_timeout,
			"unauthenticated_timeout": mail_settings.imap_unauthenticated_timeout,
			"idle_timeout": mail_settings.imap_idle_timeout,
			"cleanup_interval": mail_settings.imap_cleanup_interval,
		}

	return frappe.cache.get_value("imap_limits", generator)


def get_user_mail_account(user: str) -> str | None:
	"""Returns the mail account of the user."""

	def generator() -> str | None:
		return frappe.db.get_value("Mail Account", {"user": user, "enabled": 1}, "name")

	return frappe.cache.hget(f"user|{user}", "mail_account", generator)


def get_account_for_email(email: str) -> str | None:
	"""Returns the mail account for the email."""

	def generator() -> str | None:
		if frappe.db.exists("Mail Account", email):
			return email
		elif alias := frappe.db.exists("Mail Alias", {"email": email, "alias_for_type": "Mail Account"}):
			return frappe.db.get_value("Mail Alias", alias, "alias_for_name")

	return frappe.cache.hget(f"email|{email}", "mail_account", generator)


def get_user_mail_aliases(user: str) -> list:
	"""Returns the mail aliases of the user."""

	def generator() -> list:
		account = get_user_mail_account(user)

		if not account:
			return []

		MAIL_ALIAS = frappe.qb.DocType("Mail Alias")
		return (
			frappe.qb.from_(MAIL_ALIAS)
			.select("name")
			.where(
				(MAIL_ALIAS.enabled == 1)
				& (MAIL_ALIAS.alias_for_type == "Mail Account")
				& (MAIL_ALIAS.alias_for_name == account)
			)
		).run(pluck="name")

	return frappe.cache.hget(f"user|{user}", "mail_aliases", generator)


def get_user_default_outgoing_email(user: str) -> str | None:
	"""Returns the default outgoing email of the user."""

	def generator() -> str | None:
		return frappe.db.get_value("Mail Account", {"user": user, "enabled": 1}, "default_outgoing_email")

	return frappe.cache.hget(f"user|{user}", "default_outgoing_email", generator)


def get_blacklist_for_ip_group(ip_group: str) -> list:
	"""Returns the blacklist for the IP group."""

	def generator() -> list:
		IP_BLACKLIST = frappe.qb.DocType("IP Blacklist")
		return (
			frappe.qb.from_(IP_BLACKLIST)
			.select(
				IP_BLACKLIST.name,
				IP_BLACKLIST.is_blacklisted,
				IP_BLACKLIST.ip_address,
				IP_BLACKLIST.ip_address_expanded,
				IP_BLACKLIST.blacklist_reason,
			)
			.where(IP_BLACKLIST.ip_group == ip_group)
		).run(as_dict=True)

	return frappe.cache.get_value(f"blacklist|{ip_group}", generator)


def get_primary_agents() -> list:
	"""Returns the primary agents."""

	def generator() -> list:
		MAIL_AGENT = frappe.qb.DocType("Mail Agent")
		return (
			frappe.qb.from_(MAIL_AGENT)
			.select("name")
			.where((MAIL_AGENT.enabled == 1) & (MAIL_AGENT.is_primary == 1))
		).run(pluck="name")

	return frappe.cache.get_value("primary_agents", generator)
