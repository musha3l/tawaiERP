# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
import datetime
from datetime import date
from frappe import _
import json

@frappe.whitelist()
def get_employee(nationality ="ALL"):
	all_emp = frappe.db.sql("""select count(name) from `tabEmployee`""" )[0][0]
	saudi = frappe.db.sql("""select count(name) from `tabEmployee` where emp_nationality = "Saudi Arabia" """ )[0][0]
	non_saudi = frappe.db.sql("""select count(name) from `tabEmployee` where emp_nationality != "Saudi Arabia" """ )[0][0]
	return all_emp,saudi,non_saudi

@frappe.whitelist()
def get_latest_leaves(nationality ="ALL",**args):
	extra_condition = get_extra_condition_non_employee_table(**args)
	all_leaves = frappe.db.sql("""select employee_name,total_leave_days,workflow_state,leave_type,from_date,to_date from 
		`tabLeave Application` where 1=1 {fcond} ORDER BY creation DESC  LIMIT 10""".format(fcond=extra_condition) )
	return all_leaves

@frappe.whitelist()
def get_attendance(**args):
	extra_condition = get_extra_condition_non_employee_table(**args)
	attendance_list = frappe.db.sql("""select status as label ,count(name) as value from `tabAttendance` where 1=1 {fcond} group by status""".format(fcond=extra_condition), as_dict=1 )
	for a in attendance_list:
		a["label"] = _(a["label"])
	if not attendance_list :
		return [{"label":_("No Data"),"value":0}]
	return attendance_list

@frappe.whitelist()
def get_grade(**args):
	extra_condition = get_extra_condition(**args)
	grade_list = frappe.db.sql("""select grade as label ,count(name) as value from `tabEmployee` where 1=1 {fcond} group by grade""".format(fcond=extra_condition), as_dict=1 )
	for a in grade_list:
		a["label"] = _(a["label"])
	if not grade_list :
		return [{"label":_("No Data"),"value":0}]
	return grade_list

@frappe.whitelist()
def get_nationality(**args):
	extra_condition = get_extra_condition(**args)
	nationality_list = frappe.db.sql("""select emp_nationality as label ,count(name) as value from `tabEmployee`  where 1=1 {fcond} group by emp_nationality"""
		.format(fcond=extra_condition), as_dict=1 )
	for a in nationality_list:
		a["label"] = _(a["label"])
	if not nationality_list :
		return [{"label":_("No Data"),"value":0}]
	return nationality_list

@frappe.whitelist()
def get_gender(**args):
	extra_condition = get_extra_condition(**args)
	gender_list = frappe.db.sql("""select gender as label ,count(name) as value from `tabEmployee`  where 1=1 {fcond} group by gender""".format(fcond=extra_condition), as_dict=1 )
	for a in gender_list:
		a["label"] = _(a["label"])
	if not gender_list :
		return [{"label":_("No Data"),"value":0}]
	return gender_list

@frappe.whitelist()
def get_leaves(**args):
	extra_condition = get_extra_condition_non_employee_table(**args)

	leaves_list = frappe.db.sql("""select from_date as d , total_leave_days as leaves from `tabLeave Application` where 1=1 {fcond} group by from_date""".format(fcond=extra_condition), as_dict=1 )
	for a in leaves_list:
		a["d"] = _(a["d"])
	if not leaves_list :
		return [{"d":"1-1-2018","leaves":0}]
	return leaves_list


def get_extra_condition(**args):
	extra_condition = ""
	if args:
		for key, value in args.items():
			print("{} is {}".format(key,value))
			if key == "args":
				data = json.loads(value)
				if data != {}:
					if data["employee"] and data["employee"]!="":
						extra_condition += " and employee = '{employee}' ".format(employee=data["employee"])
					if data["department"] and data["department"]!="":
						extra_condition += " and department = '{department}' ".format(department=data["department"])
	return extra_condition
	
def get_extra_condition_non_employee_table(**args):
	extra_condition = ""
	if args:
		for key, value in args.items():
			print("{} is {}".format(key,value))
			if key == "args":
				data = json.loads(value)
				if data != {}:
					if data["employee"] and data["employee"]!="":
						extra_condition += " and employee = '{employee}' ".format(employee=data["employee"])
					if data["department"] and data["department"]!="":
						extra_condition += "  and employee in (select name from tabEmployee where department ='{department}')  ".format(department=data["department"])
	return extra_condition
