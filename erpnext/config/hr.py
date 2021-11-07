from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Employee and Attendance"),
			"items": [
				{
					"type": "doctype",
					"name": "Employee",
					"description": _("Employee records."),
				},
				{
					"type": "doctype",
					"name": "Employee Attendance Tool",
					"label": _("Employee Attendance Tool"),
					"description":_("Mark Attendance for multiple employees"),
					"hide_count": True
				},
				{
					"type": "doctype",
					"name": "Governmental Documents",
					"description": _("Governmental Documents"),
				},
				{
					"type": "doctype",
					"name": "Attendance",
					"description": _("Attendance record."),
				},
				{
					"type": "doctype",
					"name": "Upload Attendance",
					"description":_("Upload attendance from a .csv file"),
					"hide_count": True
				},
				{
					"type": "doctype",
					"name": "Grade",
					"description":_("Grade"),
					"hide_count": True
				},
			]
		},
		{
			"label": _("Employee Interface"),
			"items": [
				{
					"type": "doctype",
					"name": "General",
					"description": _("General Employee Information."),
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Attendance",
					"doctype": "Attendance"
				}
				
			]
		},
		{
			"label": _("Self Service"),
			"items": [
				{
					"type": "doctype",
					"name": "May Concern Letter",
					"label": _("May Concern Letter"),
					"description":_("May Concern Letter"),
					"hide_count": True
				},
				# {
				# 	"type": "doctype",
				# 	"name": "Employee Loan",
				# 	"description":_("Employee Loan"),
				# },
				{
					"type": "doctype",
					"name": "Employee Loan Application",
					"description":_("Employee Loan Application"),
				},
				{
					"type": "doctype",
					"name": "End of Service Award",
					"description":_("End Of Service Award"),
				},
				{
					"type": "doctype",
					"name": "Overtime Request",
					"description":_("Overtime Request"),
				},
				{
					"type": "doctype",
					"name": "Hand Over",
					"description":_("Hand Over")
				},
				{
					"type": "doctype",
					"name": "Financial Custody",
					"description":_("Financial Custody"),
				},
				{
					"type": "doctype",
					"name": "Employee Resignation",
					"description":_("Employee Resignation"),
				},
				{
					"type": "doctype",
					"name": "Promotion and Merit Increase",
					"description":_("Promotion and Merit Increase")
				},
				{
					"type": "doctype",
					"name": "Promotion and Merit",
					"label": _("Employees Promotion and Merit"),
					"description":_("Promotion and Merit")
				},
				{
					"type": "doctype",
					"name": "Employee Badge Request",
					"description":_("Employee Badge Request")
				},
				{
					"type": "doctype",
					"name": "Employee Change IBAN",
					"description":_("Employee Change IBAN")
				},
				{
					"type": "doctype",
					"name": "Health Insurance Info",
					"description":_("Health Insurance Info")
				},
				{
					"type": "doctype",
					"name": "Medical Insurance Application",
					"description": _("Medical Insurance Application."),
				},
				{
					"type": "doctype",
					"name": "Correspondence Request",
					"description": _("Correspondence Request."),
				},
			]
		},
		{
			"label": _("Leaves and Holiday"),
			"items": [
				{
					"type": "doctype",
					"name": "Leave Application",
					"description": _("Applications for leave."),
				},
				{
					"type": "doctype",
					"name": "Cancel Leave Application",
					"description":_("Cancel Leave Application")
				},
				{
					"type": "doctype",
					"name": "Return From Leave Statement",
					"description":_("Return From Leave Statement")
				},
				{
					"type": "doctype",
					"name": "Leave Claim",
					"description":_("Leave Claim")
				},
				{
					"type": "doctype",
					"name": "Exit Re Entry Application",
					"description": _("Exit Re Entry Application."),
				},
				{
					"type": "doctype",
					"name":"Leave Type",
					"description": _("Type of leaves like casual, sick etc."),
				},
				{
					"type": "doctype",
					"name": "Holiday List",
					"description": _("Holiday master.")
				},
				{
					"type": "doctype",
					"name": "Leave Allocation",
					"description": _("Allocate leaves for a period.")
				},
				{
					"type": "doctype",
					"name": "Leave Control Panel",
					"label": _("Leave Allocation Tool"),
					"description":_("Allocate leaves for the year."),
					"hide_count": True
				},
				{
					"type": "doctype",
					"name": "Leave Block List",
					"description": _("Block leave applications by department.")
				},

			]
		},
		{
			"label": _("Payroll"),
			"items": [
				{
					"type": "doctype",
					"name": "Salary Slip",
					"description": _("Monthly salary statement."),
				},
				{
					"type": "doctype",
					"name": "Process Payroll",
					"label": _("Process Payroll"),
					"description":_("Generate Salary Slips"),
					"hide_count": True
				},
				{
					"type": "doctype",
					"name": "Salary Structure",
					"description": _("Salary template master.")
				},
				{
					"type": "doctype",
					"name": "Salary Component",
					"label": _("Salary Components"),
					"description": _("Earnings, Deductions and other Salary components")
				},
				{
					"type": "doctype",
					"name": "Penalty",
					"description": _("Penalty."),
				},


			]
		},
		{
			"label": _("Recruitment"),
			"items": [
				{
					"type": "doctype",
					"name": "Job Applicant",
					"description": _("Applicant for a Job."),
				},
				{
					"type": "doctype",
					"name": "Job Opening",
					"description": _("Opening for a Job."),
				},
				{
					"type": "doctype",
					"name": "Offer Letter",
					"description": _("Offer candidate a Job."),
				},
			]
		},
		{
			"label": _("Expense Claims"),
			"items": [
				{
					"type": "doctype",
					"name": "Expense Claim",
					"description": _("Claims for company expense."),
				},
				{
					"type": "doctype",
					"name": "Expense Claim Type",
					"description": _("Types of Expense Claim.")
				},
			]
		},
		{
			"label": _("Appraisals"),
			"items": [
				{
					"type": "doctype",
					"name": "Appraisal",
					"description": _("Performance appraisal."),
				},
				{
					"type": "doctype",
					"name": "Appraisal Template",
					"description": _("Template for performance appraisals.")
				},
			]
		},
		{
			"label": _("Training and Business Trip"),
			"items": [
				{
					"type": "doctype",
					"name": "Training Trip",
					"description":_("Training Trip"),
				},
				{
					"type": "doctype",
					"name": "Business Trip",
					"description":_("Business Trip"),
				},
				# {
				# 	"type": "doctype",
				# 	"name": "Business Trip Exceptional Approval",
				# 	"description":_("Business Trip Exceptional Approval"),
				# },
				{
					"type": "doctype",
					"name": "Trip Return and Reimbursement",
					"description":_("Trip Return and Reimbursement"),
				},
				{
					"type": "doctype",
					"name": "Training Event"
				},
				# {
				# 	"type": "doctype",
				# 	"name": "Training Result"
				# },
				{
					"type": "doctype",
					"name": "Training Feedback"
				},
			]
		},

		{
			"label": _("Setup"),
			"icon": "fa fa-cog",
			"items": [
				{
					"type": "doctype",
					"name": "HR Settings",
					"description": _("Settings for HR Module")
				},
				{
					"type": "doctype",
					"name": "Employment Type",
					"description": _("Types of employment (permanent, contract, intern etc.).")
				},
				{
					"type": "doctype",
					"name": "Branch",
					"description": _("Organization branch master.")
				},
				{
					"type": "doctype",
					"label": _("Department Tree"),
					"name": "Department",
					"route": "Tree/Department",
					"description": _("Organization unit (department) master.")
				},
				{
					"type": "doctype",
					"name": "Designation",
					"description": _("Employee designation (e.g. CEO, Director etc.).")
				},
				{
					"type": "doctype",
					"name": "Loan Type",
					"description": _("Loan Type")
				},
				{
					"type": "doctype",
					"name": "Daily Work Summary Settings"
				},
			]
		},
		{
			"label": _("Reports"),
			"icon": "fa fa-list",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Leave Balance",
					"doctype": "Leave Application"
				},
				# {
				# 	"type": "report",
				# 	"is_query_report": True,
				# 	"name": "Employee Birthday",
				# 	"doctype": "Employee"
				# },
				{
					"type": "report",
					"is_query_report": True,
					"name": "Employees working on a holiday",
					"doctype": "Employee"
				},
				{
					"type": "report",
					"name": "Employee Information",
					"doctype": "Employee"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Salary Output Report",
					"label": _("Salary Output Report"),
					"doctype": "Salary Slip"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Main Salary Structure",
					"label": _("Main Salary Structure"),
					"doctype": "Salary Slip"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Monthly Attendance Sheet",
					"doctype": "Attendance"
				},

			]
		},
		{
			"label": _("Help"),
			"icon": "fa fa-facetime-video",
			"items": [
				{
					"type": "help",
					"label": _("Setting up Employees"),
					"youtube_id": "USfIUdZlUhw"
				},
				{
					"type": "help",
					"label": _("Leave Management"),
					"youtube_id": "fc0p_AXebc8"
				},
				{
					"type": "help",
					"label": _("Expense Claims"),
					"youtube_id": "5SZHJF--ZFY"
				},
				{
					"type": "help",
					"label": _("Processing Payroll"),
					"youtube_id": "apgE-f25Rm0"
				},
			]
		}
	]
