import frappe
from frappe import _

from mail.utils.user import get_user_email_addresses, has_role


@frappe.whitelist(methods=["POST"])
def validate(email: str | None = None) -> None:
	"""Validates if the user is allowed to send or receive emails."""

	if email:
		validate_user()
		validate_email_ownership(email)


def validate_user() -> None:
	"""Validates if the user is allowed to send or receive emails."""

	user = frappe.session.user

	if not has_role(user, "Mail User"):
		frappe.throw(_("User {0} is not allowed to send or receive emails.").format(frappe.bold(user)))


def validate_email_ownership(email: str) -> None:
	"""Validates if the email address is associated with the user."""

	user = frappe.session.user

	if email not in get_user_email_addresses(user):
		frappe.throw(
			_("Email address {0} is not associated with the user {1}.").format(
				frappe.bold(email), frappe.bold(user)
			)
		)
