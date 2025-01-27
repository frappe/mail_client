app_name = "mail"
app_title = "Mail"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = "Frappe Mail"
app_email = "developers@frappe.io"
app_license = "agpl-3.0"
# required_apps = []


website_redirects = [
	{
		"source": "/auth/validate",
		"target": "/api/method/mail.api.auth.validate",
		"redirect_http_status": 307,
	},
	{
		"source": "/outbound/send",
		"target": "/api/method/mail.api.outbound.send",
		"redirect_http_status": 307,
	},
	{
		"source": "/outbound/send-raw",
		"target": "/api/method/mail.api.outbound.send_raw",
		"redirect_http_status": 307,
	},
	{
		"source": "/inbound/pull",
		"target": "/api/method/mail.api.inbound.pull",
		"redirect_http_status": 307,
	},
	{
		"source": "/inbound/pull-raw",
		"target": "/api/method/mail.api.inbound.pull_raw",
		"redirect_http_status": 307,
	},
	{
		"source": "/spamd/scan",
		"target": "/api/method/mail.api.spamd.scan",
		"redirect_http_status": 307,
	},
	{
		"source": "/spamd/is-spam",
		"target": "/api/method/mail.api.spamd.is_spam",
		"redirect_http_status": 307,
	},
	{
		"source": "/spamd/score",
		"target": "/api/method/mail.api.spamd.get_spam_score",
		"redirect_http_status": 307,
	},
]

email_css = ["/assets/mail/css/email.css"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/mail/css/mail.css"
# app_include_js = "/assets/mail/js/mail.js"

# include js, css files in header of web template
# web_include_css = "/assets/mail/css/maimail.css"
# web_include_js = "/assets/mail/js/mail.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "mail/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "mail/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "mail.utils.jinja_methods",
# 	"filters": "mail.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "mail.install.before_install"
# after_install = "mail.install.after_install"
# after_migrate = "mail.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "mail.uninstall.before_uninstall"
# after_uninstall = "mail.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "mail.utils.before_app_install"
# after_app_install = "mail.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "mail.utils.before_app_uninstall"
# after_app_uninstall = "mail.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mail.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Mail Account": "mail.mail.doctype.mail_account.mail_account.get_permission_query_condition",
	"Mail Contact": "mail.mail.doctype.mail_contact.mail_contact.get_permission_query_condition",
	"Outgoing Mail": "mail.mail.doctype.outgoing_mail.outgoing_mail.get_permission_query_condition",
	"Incoming Mail": "mail.mail.doctype.incoming_mail.incoming_mail.get_permission_query_condition",
}

has_permission = {
	"Mail Account": "mail.mail.doctype.mail_account.mail_account.has_permission",
	"Mail Contact": "mail.mail.doctype.mail_contact.mail_contact.has_permission",
	"Outgoing Mail": "mail.mail.doctype.outgoing_mail.outgoing_mail.has_permission",
	"Incoming Mail": "mail.mail.doctype.incoming_mail.incoming_mail.has_permission",
}

website_route_rules = [
	{"from_route": "/mail/<path:app_path>", "to_route": "mail"},
]

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"File": {
		"validate": "mail.overrides.validate_file",
		"on_update": "mail.overrides.validate_file",
		"on_trash": "mail.overrides.validate_file",
	}
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	#     "mail.tasks.all"
	# ],
	"daily": [
		"mail.tasks.enqueue_delete_newsletters",
		"mail.mail.doctype.mail_account_request.mail_account_request.expire_mail_account_requests",
	],
	# "hourly": [
	#     "mail.tasks.hourly"
	# ],
	# "weekly": [
	#     "mail.tasks.weekly"
	# ],
	# "monthly": [
	#     "mail.tasks.monthly"
	# ],
	"cron": {
		"*/2 * * * *": [
			"mail.tasks.enqueue_transfer_failed_emails_to_agent",
			"mail.tasks.enqueue_fetch_emails_from_mail_agents",
		]
	},
}

# Testing
# -------

# before_tests = "mail.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "mail.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "mail.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

ignore_links_on_delete = ["Mail Domain", "Incoming Mail", "Outgoing Mail"]

# Request Events
# ----------------
# before_request = ["mail.utils.before_request"]
# after_request = ["mail.utils.after_request"]

# Job Events
# ----------
# before_job = ["mail.utils.before_job"]
# after_job = ["mail.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"mail.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

default_log_clearing_doctypes = {"Spam Check Log": 7}

fixtures = [
	{
		"dt": "Role",
		"filters": [["role_name", "in", ["Mail Admin", "Mail User"]]],
	},
]

add_to_apps_screen = [
	{
		"name": "mail",
		"logo": "/assets/mail/images/logo.svg",
		"title": "Mail",
		"route": "/mail",
		"has_permission": "mail.api.mail.check_app_permission",
	}
]
