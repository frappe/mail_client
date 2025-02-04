import frappe
from frappe.query_builder import Criterion, Order

from mail.utils.cache import get_account_for_user, get_domains_owned_by_tenant, get_tenant_for_user
from mail.utils.user import has_role, is_system_manager


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
		.select(OM.name, OM.subject)
		.where((OM.docstatus == 1) & (OM[searchfield].like(f"%{txt}%")))
		.orderby(OM.creation, OM.created_at, order=Order.desc)
		.offset(start)
		.limit(page_len)
	)

	if not is_system_manager(user):
		conditions = []

		if has_role(user, "Mail Admin"):
			if tenant := get_tenant_for_user(user):
				if domains := get_domains_owned_by_tenant(tenant):
					conditions.append(OM.domain_name.isin(domains))
		elif has_role(user, "Mail User"):
			if account := get_account_for_user(user):
				conditions.append(OM.sender == account)

		if not conditions:
			return []

		query = query.where(Criterion.any(conditions))

	return query.run(as_dict=False)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_users_with_mail_admin_role(
	doctype: str | None = None,
	txt: str | None = None,
	searchfield: str | None = None,
	start: int = 0,
	page_len: int = 20,
	filters: dict | None = None,
) -> list:
	"""Returns a list of User(s) who have Mail Admin role."""

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
			& (HAS_ROLE.role == "Mail Admin")
			& (HAS_ROLE.parenttype == "User")
		)
	).run(as_dict=False)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_users_with_mail_user_role(
	doctype: str | None = None,
	txt: str | None = None,
	searchfield: str | None = None,
	start: int = 0,
	page_len: int = 20,
	filters: dict | None = None,
) -> list:
	"""Returns a list of users with Mail User role."""

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
			& (HAS_ROLE.role == "Mail User")
			& (HAS_ROLE.parenttype == "User")
		)
	).run(as_dict=False)
