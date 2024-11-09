import frappe
from frappe.query_builder import Criterion, Order

from mail_client.utils.user import get_user_mailboxes, has_role, is_system_manager


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_sender(
	doctype: str | None = None,
	txt: str | None = None,
	searchfield: str | None = None,
	start: int = 0,
	page_len: int = 20,
	filters: dict | None = None,
) -> list:
	"""Returns the sender."""

	MAILBOX = frappe.qb.DocType("Mailbox")
	DOMAIN = frappe.qb.DocType("Mail Domain")
	query = (
		frappe.qb.from_(DOMAIN)
		.left_join(MAILBOX)
		.on(DOMAIN.name == MAILBOX.domain_name)
		.select(MAILBOX.name)
		.where(
			(DOMAIN.enabled == 1)
			& (DOMAIN.is_verified == 1)
			& (MAILBOX.enabled == 1)
			& (MAILBOX.outgoing == 1)
			& (MAILBOX[searchfield].like(f"%{txt}%"))
		)
		.offset(start)
		.limit(page_len)
	)

	user = frappe.session.user
	if not is_system_manager(user):
		query = query.where(MAILBOX.user == user)

	return query.run(as_dict=False)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_outgoing_mails(
	doctype: str | None = None,
	txt: str | None = None,
	searchfield: str | None = None,
	start: int = 0,
	page_len: int = 20,
	filters: dict | None = None,
) -> list:
	"""Returns Outgoing Mails on which the user has select permission."""

	user = frappe.session.user

	OM = frappe.qb.DocType("Outgoing Mail")
	query = (
		frappe.qb.from_(OM)
		.select(OM.name)
		.where((OM.docstatus == 1) & (OM[searchfield].like(f"%{txt}%")))
		.orderby(OM.creation, OM.created_at, order=Order.desc)
		.offset(start)
		.limit(page_len)
	)

	if not is_system_manager(user):
		conditions = []
		mailboxes = get_user_mailboxes(user)

		if has_role(user, "Mailbox User") and mailboxes:
			conditions.append(OM.sender.isin(mailboxes))

		if not conditions:
			return []

		query = query.where(Criterion.any(conditions))

	return query.run(as_dict=False)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_users_with_mailbox_user_role(
	doctype: str | None = None,
	txt: str | None = None,
	searchfield: str | None = None,
	start: int = 0,
	page_len: int = 20,
	filters: dict | None = None,
) -> list:
	"""Returns a list of users with Mailbox User role."""

	USER = frappe.qb.DocType("User")
	HAS_ROLE = frappe.qb.DocType("Has Role")
	return (
		frappe.qb.from_(USER)
		.left_join(HAS_ROLE)
		.on(USER.name == HAS_ROLE.parent)
		.select(USER.name)
		.where(
			(USER.enabled == 1)
			& (USER.name.like(f"%{txt}%"))
			& (HAS_ROLE.role == "Mailbox User")
			& (HAS_ROLE.parenttype == "User")
		)
	).run(as_dict=False)
