from functools import wraps

import frappe
from frappe.rate_limiter import rate_limit


def dynamic_rate_limit() -> callable:
	def decorator(fn):
		@wraps(fn)
		def wrapper(*args, **kwargs):
			method_path = frappe.form_dict.cmd
			rate_limits = get_rate_limit(method_path)

			wrapped_fn = fn
			for rl in rate_limits:
				if rl["ignore_in_developer_mode"] and frappe.conf.developer_mode:
					continue

				key = rl["key"]
				limit = rl["limit"]
				seconds = rl["seconds"]
				methods = rl["methods"].split(",")
				ip_based = bool(rl["ip_based"])
				wrapped_fn = rate_limit(key, limit, seconds, methods, ip_based)(wrapped_fn)

			return wrapped_fn(*args, **kwargs)

		return wrapper

	return decorator


def get_rate_limit(method_path: str) -> list:
	return frappe.db.get_all(
		"Rate Limit",
		filters={"enabled": 1, "method_path": method_path},
		fields=["ignore_in_developer_mode", "key", "limit", "seconds", "methods", "ip_based"],
	)
