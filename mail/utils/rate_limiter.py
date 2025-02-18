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
				rate_limits = get_rate_limits(method_path)

				for rl in rate_limits:
					if rl["ignore_in_developer_mode"] and frappe.conf.developer_mode:
						continue

					rl.pop("ignore_in_developer_mode")
					wrapped_fn = rate_limit(**rl)(wrapped_fn)

			return wrapped_fn(*args, **kwargs)

		return wrapper

	return decorator
