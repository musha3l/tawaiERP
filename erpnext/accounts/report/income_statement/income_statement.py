# -*- coding: utf-8 -*-
# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.accounts.report.financial_statements import (get_period_list, get_columns, get_data)
from erpnext.accounts.report.profit_and_loss_statement.profit_and_loss_statement import get_net_profit_loss
from erpnext.accounts.utils import get_fiscal_year

def execute(filters=None):
	period_list = get_period_list(filters.from_fiscal_year, filters.to_fiscal_year, filters.periodicity, filters.company)
	data=[]
	company_currency = frappe.db.get_value("Company", filters.company, "default_currency")
	sales_accounts = {
		"section_name": "Sales",
		"section_footer": _("Net Cash from Sales"),
		"section_header": _("Sales"),
		"account_types": [
			{"account_type": "Expence", "label": _("Total Sales")},
			{"account_type": "Expence", "label": _("Cost of  Sales")},
			{"account_type": "Expence", "label": _("Contracts Costs")},
			{"account_type": "Expence", "label": _("Cost of Unutilized Production Capacity ")},
			{"account_type": "Expence", "label": _("Gross Profit ")},
			{"account_type": "Expence", "label": _("Gross magine %")},
		]
	}
	expence_accounts = {
		"section_name": "Expence",
		"section_footer": _("Net Cash from Expence"),
		"section_header": _("Expence"),
		"account_types": [
			{"account_type": "Expence", "label": _("Selling & Distribution")},
			{"account_type": "Expence", "label": _("General & Administration")},
			{"account_type": "Expence", "label": _("Depreciation")},
			{"account_type": "Expence", "label": _("Amortization of Deferred Charges")},
		]
	}
	income_main_accounts = {
		"section_name": "Income from Main Operations",
		"section_footer": _(""),
		"section_header": _("Income from Main Operations"),
		"account_types": [
			{"account_type": "Expence", "label": _("Other Income")},
			{"account_type": "Expence", "label": _("Financial charges")},
			{"account_type": "Expence", "label": _("Income Before Zakat & Minority")},
			{"account_type": "Expence", "label": _("Income Before Zakat")},
			{"account_type": "Expence", "label": _("Zakat")},
			{"account_type": "Expence", "label": _("Net Income for the Year")},
			{"account_type": "Expence", "label": _("Profit magine %")},
		]
	}

	cash_flow_accounts = []
	cash_flow_accounts.append(sales_accounts)
	cash_flow_accounts.append(expence_accounts)
	cash_flow_accounts.append(income_main_accounts)
	

	# compute net profit / loss
	income = get_data(filters.company, "Income", "Credit", period_list, 
		accumulated_values=filters.accumulated_values, ignore_closing_entries=True, ignore_accumulated_values_for_fy= True)
	expense = get_data(filters.company, "Expense", "Debit", period_list, 
		accumulated_values=filters.accumulated_values, ignore_closing_entries=True, ignore_accumulated_values_for_fy= True)
		
	net_profit_loss = get_net_profit_loss(income, expense, period_list, filters.company)
	
	for cash_flow_account in cash_flow_accounts:
		section_data = []
		data.append({
			"account_name": cash_flow_account['section_header'], 
			"parent_account": None,
			"indent": 0.0, 
			"account": cash_flow_account['section_header']
		})
		data.append([])

		for account in cash_flow_account['account_types']:
			account_data = get_account_type_based_data(filters.company, 
				account['label'],account['account_type'], period_list, filters.accumulated_values)
			account_data.update({
				"account_name": account['label'],
				"account": account['label'], 
				"indent": 1,
				"parent_account": cash_flow_account['section_header'],
				"currency": company_currency
			})
			data.append(account_data)
			section_data.append(account_data)
		data.append([])
	


	columns = get_columns(filters.periodicity, period_list, filters.accumulated_values, filters.company)
	return columns, data

def get_account_type_based_data(company,label, account_type, period_list, accumulated_values,cost_center = None,not_to_include =None ,is_project = False):
	data = {}
	total = 0
	
	#~ #///////////////////////////////Sales  
	if label == "Total Sales":		
		for period in period_list:
			start_date = get_start_date(period, accumulated_values)
			lft, rgt = frappe.db.get_value("Account","31000000-Contract Revenue - ايرادات المشاريع - T", ["lft", "rgt"])
			command = """select sum(credit) -  sum(debit) from `tabGL Entry` where company="{0}" and posting_date >= "{1}" and posting_date <= "{2}"
					and voucher_type != 'Period Closing Voucher'
					and account in ( SELECT name FROM tabAccount WHERE root_type = "Income")
					and account in (select name from tabAccount where lft between {3} and {4})
					""".format (company,start_date if accumulated_values else period['from_date'],period['to_date'],lft,rgt)

			gl_sum = frappe.db.sql_list(command)

			if gl_sum and gl_sum[0]:
				amount = gl_sum[0]
				if account_type == "Depreciation":
					amount *= -1
			else:
				amount = 0

			total += amount
			data.setdefault(period["key"], amount)
	#~ #///////////////////////////////Expence 
	if label == "Selling & Distribution":		
		for period in period_list:
			start_date = get_start_date(period, accumulated_values)
			lft, rgt = frappe.db.get_value("Account","42100000-Dep & Amortization - الاهتلاك والاطفاء - T", ["lft", "rgt"])
			command = """select sum(credit) - sum(debit) from `tabGL Entry` where company="{0}" and posting_date >= "{1}" and posting_date <= "{2}"
					and voucher_type != 'Period Closing Voucher'
					and account in ( SELECT name FROM tabAccount WHERE root_type = "Expense")
					and account not in (select name from tabAccount where lft between {3} and {4})
					and cost_center in ("BUSINESS DEVELOPMENT - T","MARKETING - T") 
					""".format (company,start_date if accumulated_values else period['from_date'],period['to_date'],lft,rgt)

			gl_sum = frappe.db.sql_list(command)

			if gl_sum and gl_sum[0]:
				amount = gl_sum[0]
				if account_type == "Depreciation":
					amount *= -1
			else:
				amount = 0

			total += amount
			data.setdefault(period["key"], amount)
	
	if label == "General & Administration":		
		for period in period_list:
			start_date = get_start_date(period, accumulated_values)
			lft, rgt = frappe.db.get_value("Account","42100000-Dep & Amortization - الاهتلاك والاطفاء - T", ["lft", "rgt"])
			command = """select sum(credit) - sum(debit) from `tabGL Entry` where company="{0}" and posting_date >= "{1}" and posting_date <= "{2}"
					and voucher_type != 'Period Closing Voucher'
					and account in ( SELECT name FROM tabAccount WHERE root_type = "Expense")
					and account not in (select name from tabAccount where lft between {3} and {4})
					and cost_center not in ("BUSINESS DEVELOPMENT - T","MARKETING - T") 
					""".format (company,start_date if accumulated_values else period['from_date'],period['to_date'],lft,rgt)

			gl_sum = frappe.db.sql_list(command)

			if gl_sum and gl_sum[0]:
				amount = gl_sum[0]
				if account_type == "Depreciation":
					amount *= -1
			else:
				amount = 0

			total += amount
			data.setdefault(period["key"], amount)
	
	if label == "Amortization of Deferred Charges":		
		for period in period_list:
			start_date = get_start_date(period, accumulated_values)
			lft, rgt = frappe.db.get_value("Account","42100000-Dep & Amortization - الاهتلاك والاطفاء - T", ["lft", "rgt"])
			command = """select  sum(credit) - sum(debit) from `tabGL Entry` where company="{0}" and posting_date >= "{1}" and posting_date <= "{2}"
					and voucher_type != 'Period Closing Voucher'
					and account in ( SELECT name FROM tabAccount WHERE root_type = "Expense")
					and account in ("42100008-Amortization of Intangible asset - اطفاء اصول غير ملموسة  - T",
					"42100009-Amortization Leasehold Improv. - اطفاء تحسينات على مباني مستأجرة  - T")
					""".format (company,start_date if accumulated_values else period['from_date'],period['to_date'],lft,rgt)

			gl_sum = frappe.db.sql_list(command)

			if gl_sum and gl_sum[0]:
				amount = gl_sum[0]
				if account_type == "Depreciation":
					amount *= -1
			else:
				amount = 0

			total += amount
			data.setdefault(period["key"], amount)
	
	if label == "Depreciation":		
		for period in period_list:
			start_date = get_start_date(period, accumulated_values)
			lft, rgt = frappe.db.get_value("Account","42100000-Dep & Amortization - الاهتلاك والاطفاء - T", ["lft", "rgt"])
			command = """select sum(credit) - sum(debit) from `tabGL Entry` where company="{0}" and posting_date >= "{1}" and posting_date <= "{2}"
					and voucher_type != 'Period Closing Voucher'
					and account in ( SELECT name FROM tabAccount WHERE root_type = "Expense")
					and account in (select name from tabAccount where lft between {3} and {4})
					and account not in ("42100008-Amortization of Intangible asset - اطفاء اصول غير ملموسة  - T",
					"42100009-Amortization Leasehold Improv. - اطفاء تحسينات على مباني مستأجرة  - T")
					""".format (company,start_date if accumulated_values else period['from_date'],period['to_date'],lft,rgt)

			gl_sum = frappe.db.sql_list(command)

			if gl_sum and gl_sum[0]:
				amount = gl_sum[0]
				if account_type == "Depreciation":
					amount *= -1
			else:
				amount = 0

			total += amount
			data.setdefault(period["key"], amount)
	


	data["total"] = total
	return data
	
def get_start_date(period, accumulated_values):
	start_date = period["year_start_date"]
	if accumulated_values:
		start_date = get_fiscal_year(period.to_date)[1]

	return start_date

def add_total_row_account(out, data, label, period_list, currency):
	total_row = {
		"account_name": "'" + _("{0}").format(label) + "'",
		"account": "'" + _("{0}").format(label) + "'",
		"currency": currency
	}
	for row in data:
		if row.get("parent_account"):
			for period in period_list:
				total_row.setdefault(period.key, 0.0)
				total_row[period.key] += row.get(period.key, 0.0)
			
			total_row.setdefault("total", 0.0)
			total_row["total"] += row["total"]

	out.append(total_row)
	out.append({})
