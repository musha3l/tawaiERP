# encoding: utf-8
# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import formatdate, getdate, flt, add_days
from datetime import datetime
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, \
	comma_or, get_fullname, add_years, add_months, add_days, nowdate
from erpnext.hr.doctype.leave_application.leave_application import get_monthly_accumulated_leave
import datetime
# import operator
import re
from datetime import date
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, \
    comma_or, get_fullname, add_years, add_months, add_days, nowdate

from dateutil.relativedelta import relativedelta
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee



def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	return [
		_("Employee ID") + ":Link/Employee:150",
		_("Employee Name") + "::150",
		_("Department") + "::150",
		_("Date of Joining") + ":Date:150",

		_("Annual Leave - اجازة اعتيادية(Yearly)") + "::200",
		_("Annual Leave - اجازة اعتيادية(Daily)") + "::200",
		_("Sick Leave - مرضية") + "::150",
		_("Emergency -اضطرارية") + "::150",
		_("Educational - تعليمية") + "::150"

		]



# def get_conditions(filters):
# 	conditions = ""

# 	if filters.get("asset_category"): conditions += " and asset_category= '{0}' ".format(filters.get("asset_category"))

# 	# if filters.get("employee"): conditions += " and employee = %(employee)s"

# 	# if filters.get("from_date"): conditions += " and date_of_joining>=%(from_date)s"
# 	# if filters.get("to_date"): conditions += " and date_of_joining<=%(to_date)s"

# 	return conditions


def get_data(filters):
	data =[]
	# conditions = get_conditions(filters)
	li_list=frappe.db.sql(""" select name,employee_name,department,date_of_joining from `tabEmployee` where status='Active' and name not in ('EMP/1012') and name like '%EMP/1%' order by name asc""",as_dict=1)

	for emp in li_list:
		
		annual_leave=frappe.db.sql("select from_date from `tabLeave Allocation` where employee='{0}' and leave_type='Annual Leave - اجازة اعتيادية' order by creation desc limit 1".format(emp.name))
		if annual_leave:
			remain_annual = frappe.db.sql(""" select (select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'Annual Leave - اجازة اعتيادية' and docstatus =1 order by creation desc limit 1 ) - ( select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='Annual Leave - اجازة اعتيادية' and docstatus=1 and from_date >= '{1}' and to_date <= '{2}' )""".format(emp.name,annual_leave[0][0],filters.get("date")))
			max_annual = frappe.db.sql(""" select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'Annual Leave - اجازة اعتيادية' and docstatus =1 order by creation desc limit 1 """.format(emp.name))
			used_annual = frappe.db.sql(""" select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='Annual Leave - اجازة اعتيادية' and docstatus=1 and from_date >= '{1}' and to_date <= '{2}' """.format(emp.name,annual_leave[0][0],filters.get("date")))


		sick_leave=frappe.db.sql("select from_date from `tabLeave Allocation` where employee='{0}' and leave_type='Sick Leave - مرضية' order by creation desc limit 1".format(emp.name))
		if sick_leave:
			remain_sick = frappe.db.sql(""" select (select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'Sick Leave - مرضية' and docstatus =1 order by creation desc limit 1 ) - ( select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='Sick Leave - مرضية' and docstatus=1 and from_date >= '{1}' and to_date <= '{2}' )""".format(emp.name,sick_leave[0][0],filters.get("date")))
			max_sick = frappe.db.sql(""" select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'Sick Leave - مرضية' and docstatus =1 order by creation desc limit 1 """.format(emp.name))
			used_sick = frappe.db.sql(""" select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='Sick Leave - مرضية' and docstatus=1 and from_date >= '{1}' and to_date <= '{2}' """.format(emp.name,sick_leave[0][0],filters.get("date")))


		emergency_leave=frappe.db.sql("select from_date from `tabLeave Allocation` where employee='{0}' and leave_type='emergency -اضطرارية' order by creation desc limit 1".format(emp.name))
		if emergency_leave:
			remain_emergency = frappe.db.sql(""" select (select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'emergency -اضطرارية' and docstatus =1 order by creation desc limit 1 ) - ( select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='emergency -اضطرارية' and docstatus=1 and from_date >= '{1}' and to_date <= '{2}' )""".format(emp.name,emergency_leave[0][0],filters.get("date")))
			max_emergency = frappe.db.sql(""" select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'emergency -اضطرارية' and docstatus =1 order by creation desc limit 1 """.format(emp.name))
			used_emergency = frappe.db.sql(""" select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='emergency -اضطرارية' and docstatus=1 and from_date >= '{1}' and to_date <= '{2}' """.format(emp.name,emergency_leave[0][0],filters.get("date")))


		educational_leave=frappe.db.sql("select from_date from `tabLeave Allocation` where employee='{0}' and leave_type='Educational - تعليمية' order by creation desc limit 1".format(emp.name))
		if educational_leave:
			remain_educational = frappe.db.sql(""" select (select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'Educational - تعليمية' and docstatus =1 order by creation desc limit 1 ) - ( select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='Educational - تعليمية' and docstatus=1 and from_date >= '{1}' and to_date <= '{2}' )""".format(emp.name,educational_leave[0][0],filters.get("date")))
			max_educational = frappe.db.sql(""" select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'Educational - تعليمية' and docstatus =1 order by creation desc limit 1 """.format(emp.name))
			used_educational = frappe.db.sql(""" select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='Educational - تعليمية' and docstatus=1 and from_date >= '{1}' and to_date <= '{2}' """.format(emp.name,educational_leave[0][0],filters.get("date")))

		try:
			if used_annual[0][0] and annual_leave[0][0]:
				annual_leave_balance = remain_annual[0][0]
			elif max_annual[0][0]:
				annual_leave_balance = max_annual[0][0]
		except:
			annual_leave_balance = 0


		try:
			if used_sick[0][0] and sick_leave[0][0]:
				sick_leave_balance = remain_sick[0][0]
			elif max_sick[0][0]:
				sick_leave_balance = max_sick[0][0]
		except:
			sick_leave_balance = 0



		try:
			if used_emergency[0][0] and emergency_leave[0][0]:
				emergency_leave_balance = remain_emergency[0][0]
			elif max_sick[0][0]:
				emergency_leave_balance = max_emergency[0][0]
		except:
			emergency_leave_balance = 0



		try:
			if used_educational[0][0] and educational_leave[0][0]:
				educational_leave_balance = remain_educational[0][0]
			elif max_sick[0][0]:
				educational_leave_balance = max_educational[0][0]
		except:
			educational_leave_balance = 0

			


		row = [
		emp.name,
		emp.employee_name,
		emp.department,
		emp.date_of_joining,

		annual_leave_balance,
		get_monthly_accumulated_leave(filters.get("date"),filters.get("date"),'Annual Leave - اجازة اعتيادية',emp.name),
		sick_leave_balance,
		emergency_leave_balance,
		educational_leave_balance,
		
    	]
		data.append(row)
		

	return data

