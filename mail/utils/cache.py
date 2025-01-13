import frappe
from frappe import _


def get_root_domain_name() -> str | None:
	"""Returns the root domain name."""

	def generator() -> str | None:
		return frappe.db.get_single_value("Mail Settings", "root_domain_name")

	return frappe.cache.get_value("root_domain_name", generator)


def get_smtp_limits() -> dict:
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


def get_postmaster_for_domain(domain_name: str) -> str:
	"""Returns the postmaster for the domain."""

	def generator() -> str:
		postmaster = frappe.db.get_value(
			"Mailbox",
			{
				"enabled": 1,
				"outgoing": 1,
				"postmaster": 1,
				"domain_name": domain_name,
				"user": "Administrator",
			},
			"name",
		)

		if not postmaster:
			frappe.throw(_("Postmaster not found for {0}").format(domain_name))

		return postmaster

	return frappe.cache.get_value(f"postmaster|{domain_name}", generator)


def get_user_owned_domains(user: str) -> list:
	"""Returns the domains owned by the user."""

	def generator() -> list:
		MAIL_DOMAIN = frappe.qb.DocType("Mail Domain")
		return (
			frappe.qb.from_(MAIL_DOMAIN)
			.select("name")
			.where((MAIL_DOMAIN.enabled == 1) & (MAIL_DOMAIN.domain_owner == user))
		).run(pluck="name")

	return frappe.cache.hget(f"user|{user}", "owned_domains", generator)


def get_user_mail_accounts(user: str) -> list:
	def generator() -> list:
		MAIL_ACCOUNT = frappe.qb.DocType("Mail Account")
		return (
			frappe.qb.from_(MAIL_ACCOUNT)
			.select("name")
			.where((MAIL_ACCOUNT.enabled == 1) & (MAIL_ACCOUNT.user == user))
		).run(pluck="name")

	return frappe.cache.hget(f"user|{user}", "mail_accounts", generator)


def get_user_mail_aliases(user: str) -> list:
	def generator() -> list:
		accounts = get_user_mail_accounts(user)

		if not accounts:
			return []

		MAIL_ALIAS = frappe.qb.DocType("Mail Alias")
		return (
			frappe.qb.from_(MAIL_ALIAS)
			.select("name")
			.where(
				(MAIL_ALIAS.enabled == 1)
				& (MAIL_ALIAS.alias_for_type == "Mail Account")
				& (MAIL_ALIAS.alias_for_name.isin(accounts))
			)
		).run(pluck="name")

	return frappe.cache.hget(f"user|{user}", "mail_aliases", generator)


def get_user_incoming_mailboxes(user: str) -> list:
	"""Returns the incoming mailboxes of the user."""

	def generator() -> list:
		MAILBOX = frappe.qb.DocType("Mailbox")
		return (
			frappe.qb.from_(MAILBOX)
			.select("name")
			.where((MAILBOX.user == user) & (MAILBOX.enabled == 1) & (MAILBOX.incoming == 1))
		).run(pluck="name")

	return frappe.cache.hget(f"user|{user}", "incoming_mailboxes", generator)


def get_user_outgoing_mailboxes(user: str) -> list:
	"""Returns the outgoing mailboxes of the user."""

	def generator() -> list:
		MAILBOX = frappe.qb.DocType("Mailbox")
		return (
			frappe.qb.from_(MAILBOX)
			.select("name")
			.where((MAILBOX.user == user) & (MAILBOX.enabled == 1) & (MAILBOX.outgoing == 1))
		).run(pluck="name")

	return frappe.cache.hget(f"user|{user}", "outgoing_mailboxes", generator)


def get_user_default_mail_account(user: str) -> str | None:
	"""Returns the default mail account of the user."""

	def generator() -> str | None:
		return frappe.db.get_value("Mail Account", {"user": user, "enabled": 1, "is_default": 1}, "name")

	return frappe.cache.hget(f"user|{user}", "default_mail_account", generator)


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
