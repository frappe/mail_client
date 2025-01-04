import socket

import dns.resolver
import frappe
from frappe import _


def get_dns_record(fqdn: str, type: str = "A", raise_exception: bool = False) -> dns.resolver.Answer | None:
	"""Returns DNS record for the given FQDN and type."""

	err_msg = None

	try:
		resolver = dns.resolver.Resolver(configure=False)
		resolver.nameservers = [
			"1.1.1.1",
			"8.8.4.4",
			"8.8.8.8",
			"9.9.9.9",
		]

		r = resolver.resolve(fqdn, type)
		return r
	except dns.resolver.NXDOMAIN:
		err_msg = _("{0} does not exist.").format(frappe.bold(fqdn))
	except dns.resolver.NoAnswer:
		err_msg = _("No answer for {0}.").format(frappe.bold(fqdn))
	except dns.exception.DNSException as e:
		err_msg = _(str(e))

	if raise_exception and err_msg:
		frappe.throw(err_msg)


def get_host_by_ip(ip_address: str, raise_exception: bool = False) -> str | None:
	"""Returns host for the given IP address."""

	err_msg = None

	try:
		return socket.gethostbyaddr(ip_address)[0]
	except Exception as e:
		err_msg = _(str(e))

	if raise_exception and err_msg:
		frappe.throw(err_msg)


def verify_dns_record(fqdn: str, type: str, expected_value: str, debug: bool = False) -> bool:
	"""Verifies the DNS Record."""

	if result := get_dns_record(fqdn, type):
		for data in result:
			if data:
				if type == "MX":
					data = data.exchange
				data = data.to_text().replace('"', "")
				if type == "TXT" and "._domainkey." in fqdn:
					data = data.replace(" ", "")
					expected_value = expected_value.replace(" ", "")
				if data == expected_value:
					return True
			if debug:
				frappe.msgprint(f"Expected: {expected_value} Got: {data}")
	return False
