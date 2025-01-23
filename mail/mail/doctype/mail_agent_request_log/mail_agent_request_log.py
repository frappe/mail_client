# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from urllib.parse import quote

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, time_diff_in_seconds


class MailAgentRequestLog(Document):
	def validate(self) -> None:
		self.validate_agent()
		self.validate_endpoint()

	def after_insert(self) -> None:
		self.execute()

	def validate_agent(self) -> None:
		"""Validate if the agent is enabled."""

		if not frappe.get_cached_value("Mail Agent", self.agent, "enabled"):
			frappe.throw(_("Mail Agent {0} is disabled.").format(self.agent))

	def validate_endpoint(self) -> None:
		"""Validates the endpoint."""

		self.endpoint = quote(self.endpoint)

	def execute(self) -> None:
		"""Executes the job."""

		from mail.agent import AgentAPI

		self.started_at = now()

		try:
			agent = frappe.get_cached_doc("Mail Agent", self.agent)

			if not agent.enabled:
				frappe.throw(_("Mail Agent {0} is disabled.").format(self.agent))

			agent_api = AgentAPI(
				agent.base_url,
				api_key=agent.get_password("api_key"),
				username=agent.username,
				password=agent.get_password("password"),
			)
			response = agent_api.request(
				method=self.method,
				endpoint=self.endpoint,
				params=self.request_params,
				data=self.request_data,
				json=self.request_json,
				headers=self.request_headers,
			)

			self.status = "Completed"
			if response.get("error"):
				self.status = "Failed"

			self.response_json = response
		except Exception:
			self.status = "Failed"
			self.error_log = frappe.get_traceback()
		finally:
			self.ended_at = now()
			self.duration = time_diff_in_seconds(self.ended_at, self.started_at)
			self.db_update()


def create_mail_agent_request_log(
	agent: str,
	method: str,
	endpoint: str,
	request_headers: dict | None = None,
	request_params: dict | None = None,
	request_data: str | None = None,
	request_json: dict | None = None,
) -> "MailAgentRequestLog":
	"""Creates a new Mail Agent Request Log."""

	agent_request_log = frappe.new_doc("Mail Agent Request Log")
	agent_request_log.agent = agent
	agent_request_log.method = method
	agent_request_log.endpoint = endpoint
	agent_request_log.request_headers = request_headers
	agent_request_log.request_params = request_params
	agent_request_log.request_data = request_data
	agent_request_log.request_json = request_json
	agent_request_log.insert()

	return agent_request_log
