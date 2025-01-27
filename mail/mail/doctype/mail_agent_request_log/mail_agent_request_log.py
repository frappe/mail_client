# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import json
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
		if frappe.flags.do_not_enqueue:
			self.execute()
		else:
			frappe.enqueue_doc(
				self.doctype,
				self.name,
				"execute",
				enqueue_after_commit=True,
			)

	def validate_agent(self) -> None:
		"""Validate if the agent is enabled."""

		if not frappe.get_cached_value("Mail Agent", self.agent, "enabled"):
			frappe.throw(_("Mail Agent {0} is disabled.").format(self.agent))

	def validate_endpoint(self) -> None:
		"""Validates the endpoint."""

		self.endpoint = quote(self.endpoint)

	def execute(self) -> None:
		"""Executes the job."""

		started_at = now()
		self._db_set(status="Running", started_at=started_at, commit=True)

		kwargs = {}
		try:
			self._execute_method_on_start()
			self._execute_request()
			self._execute_method_on_end()
			kwargs["status"] = "Completed"
		except Exception:
			error_log = frappe.get_traceback(with_context=True)
			kwargs["error_log"] = error_log
			kwargs["status"] = "Failed"
		finally:
			kwargs["ended_at"] = now()
			kwargs["duration"] = time_diff_in_seconds(kwargs["ended_at"], started_at)
			self._db_set(**kwargs, commit=True)

	def _execute_method_on_start(self) -> None:
		"""Executes the method on start."""

		if self.execute_on_start:
			method = frappe.get_attr(self.execute_on_start)
			method(self)

	def _execute_request(self) -> None:
		"""Executes the request."""

		agent = frappe.get_cached_doc("Mail Agent", self.agent)

		if not agent.enabled:
			frappe.throw(_("Mail Agent {0} is disabled.").format(self.agent))

		from mail.agent import AgentAPI

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

		response_json = json.dumps(response.json())
		if response.status_code == 200:
			self._db_set(response_json=response_json)
		else:
			frappe.throw(title=_("Agent Request Failed"), msg=response_json)

	def _execute_method_on_end(self) -> None:
		"""Executes the method on end."""

		if self.execute_on_end:
			method = frappe.get_attr(self.execute_on_end)
			method(self)

	def _db_set(
		self,
		update_modified: bool = True,
		commit: bool = False,
		notify_update: bool = False,
		**kwargs,
	) -> None:
		"""Updates the document with the given key-value pairs."""

		self.db_set(kwargs, update_modified=update_modified, commit=commit)

		if notify_update:
			self.notify_update()


def create_mail_agent_request_log(
	agent: str,
	method: str,
	endpoint: str,
	request_headers: dict | None = None,
	request_params: dict | None = None,
	request_data: str | None = None,
	request_json: dict | None = None,
	do_not_enqueue: bool = False,
) -> "MailAgentRequestLog":
	"""Creates a new Mail Agent Request Log."""

	if do_not_enqueue:
		frappe.flags.do_not_enqueue = True

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
