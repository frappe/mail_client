from functools import wraps

import frappe
from frappe.rate_limiter import rate_limit

from mail.utils.cache import get_rate_limits


def dynamic_rate_limit() -> callable:
	"""A decorator to apply rate limits dynamically based on the method path."""

	def decorator(fn):
		@wraps(fn)
		def wrapper(*args, **kwargs):
			wrapped_fn = fn
			if method_path := frappe.form_dict.cmd:
				request_ip = frappe.local.request_ip
				rate_limits = get_rate_limits(method_path)

				for rl in rate_limits:
					if rl["ignore_in_developer_mode"] and frappe.conf.developer_mode:
						continue
					elif rl["ip_based"] and any(
						request_ip.startswith(prefix) for prefix in rl["ignored_ips"]
					):
						continue

					wrapped_fn = rate_limit(
						key=rl["key"],
						limit=rl["limit"],
						seconds=rl["seconds"],
						methods=rl["methods"],
						ip_based=rl["ip_based"],
					)(wrapped_fn)

			return wrapped_fn(*args, **kwargs)

		return wrapper

	return decorator
