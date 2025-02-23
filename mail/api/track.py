import frappe
from frappe import _
from frappe.query_builder import Case

from mail.utils.rate_limiter import dynamic_rate_limit


@frappe.whitelist(methods=["GET"], allow_guest=True)
@dynamic_rate_limit()
def open() -> None:
	"""Updates Outgoing Mail opened status."""

	try:
		id = frappe.request.args.get("id")

		if not id:
			frappe.throw(_("Tracking ID is required - {0}.").format(frappe.local.request_ip))

		now = frappe.utils.now()
		OM = frappe.qb.DocType("Outgoing Mail")
		(
			frappe.qb.update(OM)
			.set(
				OM.first_opened_at,
				Case().when(OM.first_opened_at.isnull(), now).else_(OM.first_opened_at),
			)
			.set(OM.last_opened_at, now)
			.set(OM.open_count, OM.open_count + 1)
			.set(OM.last_opened_from_ip, frappe.local.request_ip)
			.where((OM.docstatus == 1) & (OM.tracking_id == id))
		).run()
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="mail.api.track.open", message=frappe.get_traceback())
	finally:
		frappe.response.update(frappe.utils.get_imaginary_pixel_response())
