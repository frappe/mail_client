import frappe
from frappe import _

from mail.utils.user import has_role, is_mail_account_owner


@frappe.whitelist(methods=["POST"])
def validate(account: str | None = None) -> None:
	"""Validates the account for inbound and outbound emails."""

	if account:
		validate_user()
		validate_account(account)


def validate_user() -> None:
	"""Validates if the user has the required role to access mail accounts."""

	user = frappe.session.user

	if not has_role(user, "Mail User"):
		frappe.throw(_("User {0} is not allowed to access mail accounts.").format(frappe.bold(user)))


def validate_account(account: str) -> None:
	"""Validates if the mail account is associated with the user."""

	user = frappe.session.user

	if not is_mail_account_owner(account, user):
		frappe.throw(
			_("Mail Account {0} is not associated with user {1}").format(
				frappe.bold(account), frappe.bold(user)
			)
		)
