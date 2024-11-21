# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from datetime import datetime, timezone

import frappe
import xmltodict
from frappe.model.document import Document
from frappe.utils import cint, convert_utc_to_system_timezone, get_datetime_str


class DMARCReport(Document):
	pass


def create_dmarc_report(xml_content: str) -> "DMARCReport":
	"""Create a DMARC Report from the given XML content."""

	root = xmltodict.parse(xml_content)
	feedback = root["feedback"]

	report_metadata = feedback["report_metadata"]
	policy_published = feedback["policy_published"]
	records = feedback["record"]

	doc = frappe.new_doc("DMARC Report")
	doc.organization = report_metadata["org_name"]
	doc.email = report_metadata["email"]
	doc.report_id = report_metadata["report_id"]
	doc.extra_contact_info = report_metadata.get("extra_contact_info", "")  # Optional

	date_range = report_metadata["date_range"]
	doc.from_date = get_datetime_str(
		convert_utc_to_system_timezone(datetime.fromtimestamp(int(date_range["begin"]), tz=timezone.utc))
	)
	doc.to_date = get_datetime_str(
		convert_utc_to_system_timezone(datetime.fromtimestamp(int(date_range["end"]), tz=timezone.utc))
	)

	doc.domain_name = policy_published["domain"]
	doc.policy_published = json.dumps(
		{
			"adkim": policy_published["adkim"],
			"aspf": policy_published["aspf"],
			"p": policy_published["p"],
			"sp": policy_published.get("sp", ""),  # Optional
			"pct": policy_published.get("pct", ""),  # Optional
			"np": policy_published.get("np", ""),  # Optional
			"fo": policy_published.get("fo", ""),  # Optional
		},
		indent=4,
	)

	if isinstance(records, dict):
		records = [records]

	for record in records:
		row = record["row"]
		policy_evaluated = row["policy_evaluated"]
		identifiers = record["identifiers"]
		auth_results = record["auth_results"]

		source_ip = row["source_ip"]
		count = row["count"]
		disposition = policy_evaluated["disposition"]
		dkim_result = policy_evaluated["dkim"].upper()
		spf_result = policy_evaluated["spf"].upper()
		header_from = identifiers["header_from"]

		results = []
		for auth_type, auth_result in auth_results.items():
			if isinstance(auth_result, dict):
				auth_result = [auth_result]

			for result in auth_result:
				result["auth_type"] = auth_type.upper()
				result["result"] = result["result"].upper()
				results.append(result)

		doc.append(
			"records",
			{
				"source_ip": source_ip,
				"count": cint(count),
				"disposition": disposition,
				"dkim_result": dkim_result,
				"spf_result": spf_result,
				"header_from": header_from,
				"auth_results": json.dumps(results, indent=4),
			},
		)

	doc.flags.ignore_links = True

	try:
		doc.insert(ignore_permissions=True, ignore_if_duplicate=True)
		return doc
	except frappe.UniqueValidationError:
		frappe.log_error(
			title="Duplicate DMARC Report",
			message=frappe.get_traceback(with_context=True),
		)
		return frappe.get_doc("DMARC Report", {"report_id": doc.report_id})
