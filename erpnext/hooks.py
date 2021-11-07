from __future__ import unicode_literals
from frappe import _
from . import __version__ as app_version

app_name = "erpnext"
app_title = "ERPNext"
app_publisher = "Frappe Technologies Pvt. Ltd."
app_description = """ERP made simple"""
app_icon = "fa fa-th"
app_color = "#e74c3c"
app_email = "info@erpnext.com"
app_license = "GNU General Public License (v3)"
source_link = "https://github.com/frappe/erpnext"

error_report_email = "support@erpnext.com"

app_include_js = [
		"assets/js/erpnext.min.js",
		'assets/erpnext/assets/plugins/morris/raphael.min.js',
		'assets/erpnext/assets/plugins/morris/morris.min.js',
		'assets/erpnext/assets/plugins/morris/morris-data.js',
		'assets/erpnext/assets/plugins/lobipanel/lobipanel.min.js',
		'assets/erpnext/assets/plugins/fastclick/fastclick.min.js',
		'assets/erpnext/assets/plugins/toastr/toastr.min.js',
		'assets/erpnext/assets/plugins/sparkline/sparkline.min.js',
		'assets/erpnext/assets/plugins/counterup/jquery.counterup.min.js',
		'assets/erpnext/assets/plugins/counterup/waypoints.js',
		'assets/erpnext/assets/plugins/emojionearea/emojionearea.min.js',
		'assets/erpnext/assets/plugins/monthly/monthly.min.js',
		'assets/erpnext/assets/plugins/footable-bootstrap/js/footable.all.min.js',
		'assets/erpnext/assets/dist/js/page/dashboard2.js',
		'assets/erpnext/assets/dist/js/page/theme.js',
		]
app_include_css = [
		"assets/css/erpnext.css",
		'assets/erpnext/assets/plugins/morris/morris.css',
		"assets/erpnext/css/component_ui.css",
		"assets/erpnext/css/component_ui_projects.css",
]
#~ 'assets/erpnext/assets/dist/css/base.css',
#~ 'assets/erpnext/assets/dist/css/base_rtl.css',
#~ 'assets/erpnext/assets/dist/css/style.css',

web_include_js = "assets/js/erpnext-web.min.js"
web_include_css = "assets/erpnext/css/website.css"

# setup wizard
setup_wizard_requires = "assets/erpnext/js/setup_wizard.js"
setup_wizard_complete = "erpnext.setup.setup_wizard.setup_wizard.setup_complete"

before_install = "erpnext.setup.install.check_setup_wizard_not_completed"
after_install = "erpnext.setup.install.after_install"

boot_session = "erpnext.startup.boot.boot_session"
notification_config = "erpnext.startup.notifications.get_notification_config"
get_help_messages = "erpnext.utilities.activation.get_help_messages"

on_session_creation = "erpnext.shopping_cart.utils.set_cart_count"
on_logout = "erpnext.shopping_cart.utils.clear_cart_count"

treeviews = ['Account', 'Cost Center', 'Warehouse', 'Item Group', 'Customer Group', 'Sales Person', 'Territory', "BOM","Department","Asset Category"]

# website
update_website_context = "erpnext.shopping_cart.utils.update_website_context"
my_account_context = "erpnext.shopping_cart.utils.update_my_account_context"

email_append_to = ["Job Applicant", "Opportunity", "Issue"]

calendars = ["Task", "Production Order", "Leave Application", "Sales Order", "Holiday List", "Over Time", "Planning"]

fixtures = ["Web Form"]

website_generators = ["Item Group", "Item", "Sales Partner", "Job Opening", "Student Admission"]

website_context = {
	"favicon": 	"/assets/erpnext/images/favicon.png",
	"splash_image": "/assets/erpnext/images/splash.png"
}

website_route_rules = [
	{"from_route": "/orders", "to_route": "Sales Order"},
	{"from_route": "/orders/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Sales Order",
			"parents": [{"title": _("Orders"), "name": "orders"}]
		}
	},
	{"from_route": "/invoices", "to_route": "Sales Invoice"},
	{"from_route": "/invoices/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Sales Invoice",
			"parents": [{"title": _("Invoices"), "name": "invoices"}]
		}
	},
	{"from_route": "/quotations", "to_route": "Supplier Quotation"},
	{"from_route": "/quotations/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Supplier Quotation",
			"parents": [{"title": _("Supplier Quotation"), "name": "quotations"}]
		}
	},
	{"from_route": "/shipments", "to_route": "Delivery Note"},
	{"from_route": "/shipments/<path:name>", "to_route": "order",
		"defaults": {
			"doctype": "Delivery Note",
			"parents": [{"title": _("Shipments"), "name": "shipments"}]
		}
	},
	{"from_route": "/rfq", "to_route": "Request for Quotation"},
	{"from_route": "/rfq/<path:name>", "to_route": "rfq",
		"defaults": {
			"doctype": "Request for Quotation",
			"parents": [{"title": _("Request for Quotation"), "name": "rfq"}]
		}
	},
	{"from_route": "/addresses", "to_route": "Address"},
	{"from_route": "/addresses/<path:name>", "to_route": "addresses",
		"defaults": {
			"doctype": "Address",
			"parents": [{"title": _("Addresses"), "name": "addresses"}]
		}
	},
	{"from_route": "/jobs", "to_route": "Job Opening"},
	{"from_route": "/admissions", "to_route": "Student Admission"},
]

portal_menu_items = [
	{"title": _("Projects"), "route": "/project", "reference_doctype": "Project"},
	{"title": _("Request for Quotations"), "route": "/rfq", "reference_doctype": "Request for Quotation", "role": "Supplier"},
	{"title": _("Supplier Quotation"), "route": "/quotations", "reference_doctype": "Supplier Quotation", "role": "Supplier"},
	{"title": _("Orders"), "route": "/orders", "reference_doctype": "Sales Order", "role":"Customer"},
	{"title": _("Invoices"), "route": "/invoices", "reference_doctype": "Sales Invoice", "role":"Customer"},
	{"title": _("Shipments"), "route": "/shipments", "reference_doctype": "Delivery Note", "role":"Customer"},
	{"title": _("Issues"), "route": "/issues", "reference_doctype": "Issue", "role":"Customer"},
	{"title": _("Addresses"), "route": "/addresses", "reference_doctype": "Address"},
	{"title": _("Announcements"), "route": "/announcement", "reference_doctype": "Announcement"},
	{"title": _("Courses"), "route": "/course", "reference_doctype": "Course", "role":"Student"},
	{"title": _("Assessment Schedule"), "route": "/assessment", "reference_doctype": "Assessment", "role":"Student"},
	{"title": _("Fees"), "route": "/fees", "reference_doctype": "Fees", "role":"Student"}
]

default_roles = [
	{'role': 'Customer', 'doctype':'Contact', 'email_field': 'email_id',
		'filters': {'ifnull(customer, "")': ('!=', '')}},
	{'role': 'Supplier', 'doctype':'Contact', 'email_field': 'email_id',
		'filters': {'ifnull(supplier, "")': ('!=', '')}},
	{'role': 'Student', 'doctype':'Student', 'email_field': 'student_email_id'}
]

has_website_permission = {
	"Sales Order": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Sales Invoice": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Supplier Quotation": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Delivery Note": "erpnext.controllers.website_list_for_contact.has_website_permission",
	"Issue": "erpnext.support.doctype.issue.issue.has_website_permission",
	"Address": "erpnext.utilities.doctype.address.address.has_website_permission",
	"Discussion": "erpnext.schools.web_form.discussion.discussion.has_website_permission"
}

permission_query_conditions = {
	"Cost Center": "erpnext.accounts.doctype.cost_center.cost_center.get_permission_query_conditions",
	"Contact": "erpnext.utilities.address_and_contact.get_permission_query_conditions_for_contact",
	"Address": "erpnext.utilities.address_and_contact.get_permission_query_conditions_for_address",
	"Leave Application": "erpnext.hr.doctype.leave_application.leave_application.get_permission_query_conditions",
	"Job Assignment": "erpnext.hr.doctype.job_assignment.job_assignment.get_permission_query_conditions",
	"Financial Custody": "erpnext.hr.doctype.financial_custody.financial_custody.get_permission_query_conditions",
	"Over Time": "erpnext.hr.doctype.over_time.over_time.get_permission_query_conditions",
	"Salary Slip": "erpnext.hr.doctype.salary_slip.salary_slip.get_permission_query_conditions",
	"Salary Structure": "erpnext.hr.doctype.salary_structure.salary_structure.get_permission_query_conditions",
	"Return From Leave Statement": "erpnext.hr.doctype.return_from_leave_statement.return_from_leave_statement.get_permission_query_conditions",
	"Employee Badge Request": "erpnext.hr.doctype.employee_badge_request.employee_badge_request.get_permission_query_conditions",
	"Employee Change IBAN": "erpnext.hr.doctype.employee_change_iban.employee_change_iban.get_permission_query_conditions",
	"Medical Insurance Application": "erpnext.hr.doctype.medical_insurance_application.medical_insurance_application.get_permission_query_conditions",
	"Governmental Documents": "erpnext.hr.doctype.governmental_documents.governmental_documents.get_permission_query_conditions",
	"May Concern Letter": "erpnext.hr.doctype.may_concern_letter.may_concern_letter.get_permission_query_conditions",
	"End of Service Award": "erpnext.hr.doctype.end_of_service_award.end_of_service_award.get_permission_query_conditions",
	"Overtime Request": "erpnext.hr.doctype.overtime_request.overtime_request.get_permission_query_conditions",
	"Employee Resignation": "erpnext.hr.doctype.employee_resignation.employee_resignation.get_permission_query_conditions",
	"Cancel Leave Application": "erpnext.hr.doctype.cancel_leave_application.cancel_leave_application.get_permission_query_conditions",
	"Expense Claim": "erpnext.hr.doctype.expense_claim.expense_claim.get_permission_query_conditions",
	"Administrative Decision":"erpnext.administrative_communication.doctype.administrative_decision.administrative_decision.get_permission_query_conditions",

}

has_permission = {
	"Contact": "erpnext.utilities.address_and_contact.has_permission",
	"Address": "erpnext.utilities.address_and_contact.has_permission",
	"Leave Application":"erpnext.hr.doctype.leave_application.leave_application.has_permission",
	"Overtime Request": "erpnext.hr.doctype.overtime_request.overtime_request.has_permission",
	"Administrative Decision":"erpnext.administrative_communication.doctype.administrative_decision.administrative_decision.has_permission",

}

dump_report_map = "erpnext.startup.report_data_map.data_map"

before_tests = "erpnext.setup.utils.before_tests"

standard_queries = {
	"Customer": "erpnext.selling.doctype.customer.customer.get_customer_list"
}

doc_events = {
	"*": {
		"validate": "erpnext.controllers.queries.update_custom_field",
        "on_update": "erpnext.setup.doctype.user_notification.user_notification.set_notifications",
        "on_submit": "erpnext.setup.doctype.user_notification.user_notification.set_notifications"

    },
	"Stock Entry": {
		"on_submit": "erpnext.stock.doctype.material_request.material_request.update_completed_and_requested_qty",
		"on_cancel": "erpnext.stock.doctype.material_request.material_request.update_completed_and_requested_qty"
	},
	"User": {
		"validate": "erpnext.hr.doctype.employee.employee.validate_employee_role",
		"on_update": "erpnext.hr.doctype.employee.employee.update_user_permissions",
		"on_update": "erpnext.utilities.doctype.contact.contact.update_contact"
	},
	("Sales Taxes and Charges Template", 'Price List'): {
		"on_update": "erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings.validate_cart_settings"
	},
	"Address": {
		"validate": "erpnext.shopping_cart.cart.set_customer_in_address"
	},

	# bubble transaction notification on master
	('Opportunity', 'Quotation', 'Sales Order', 'Delivery Note', 'Sales Invoice',
		'Supplier Quotation', 'Purchase Order', 'Purchase Receipt',
		'Purchase Invoice', 'Project', 'Issue'): {
			'on_change': 'erpnext.accounts.party_status.notify_status'
		},

	"Website Settings": {
		"validate": "erpnext.portal.doctype.products_settings.products_settings.home_page_is_products"
	},
	"Payment Entry": {
		"on_submit": "erpnext.accounts.doctype.payment_request.payment_request.make_status_as_paid"
	}
}

scheduler_events = {
	"hourly": [
		"erpnext.controllers.recurring_document.create_recurring_documents",
		'erpnext.hr.doctype.daily_work_summary_settings.daily_work_summary_settings.trigger_emails',
		"erpnext.hr.doctype.governmental_documents.governmental_documents.hooked_validate_notification_message",
		"erpnext.hr.doctype.employee.employee.hooked_validate_exp_dates"
	],
	"daily": [
		"erpnext.tools.validate_notifications",
		"erpnext.tools.validate_handled_notifications",
		"erpnext.stock.reorder_item.reorder_item",
		"erpnext.setup.doctype.email_digest.email_digest.send",
		"erpnext.support.doctype.issue.issue.auto_close_tickets",
		"erpnext.controllers.accounts_controller.update_invoice_status",
		"erpnext.accounts.doctype.fiscal_year.fiscal_year.auto_create_fiscal_year",
		# "erpnext.hr.doctype.employee.employee.send_birthday_reminders",
		"erpnext.projects.doctype.task.task.set_tasks_as_overdue",
		"erpnext.hr.doctype.health_insurance_info.health_insurance_info.hooked_validate_exp_date",
		#~ "erpnext.accounts.doctype.asset.depreciation.post_depreciation_entries",
		'erpnext.hr.doctype.daily_work_summary_settings.daily_work_summary_settings.send_summary',
		'erpnext.hr.doctype.attendance.attendance.validate_absence_and_notify',
		'erpnext.hr.doctype.leave_application.leave_application.hooked_leave_allocation_builder',
		'erpnext.hr.doctype.leave_application.leave_application.increase_daily_leave_balance',
		# 'erpnext.hr.doctype.leave_application.leave_application.calculate_truncated_days',
		'erpnext.hr.doctype.leave_allocation.leave_allocation.check_max_allocation_balance',
		'erpnext.hr.doctype.employee.employee.passport_validate_check',
		'erpnext.hr.doctype.salary_structure.salary_structure.set_salary_structure_active',
		# 'erpnext.hr.doctype.appraisal.appraisal.appraisal_creation_and_contacting_manager'
		# 'erpnext.hr.doctype.leave_application.leave_application.create_return_from_leave_statement_after_leave'
	]
}

default_mail_footer = """<div style="text-align: center;">
	<a href="https://erpnext.com?source=via_email_footer" target="_blank" style="color: #8d99a6;">
		Sent via Tawari ERP
	</a>
</div>"""

get_translated_dict = {
	("doctype", "Global Defaults"): "frappe.geo.country_info.get_translated_dict"
}

bot_parsers = [
	'erpnext.utilities.bot.FindItemBot',
]

get_site_info = 'erpnext.utilities.get_site_info'

payment_gateway_enabled = "erpnext.accounts.utils.create_payment_gateway_and_account"
