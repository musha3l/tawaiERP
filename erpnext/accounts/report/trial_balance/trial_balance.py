# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, cstr
from erpnext.accounts.report.financial_statements \
	import filter_accounts, set_gl_entries_by_account, filter_out_zero_value_rows

value_fields = ("opening_debit", "opening_credit", "debit", "credit", "closing_debit", "closing_credit")

def execute(filters=None):
	validate_filters(filters)
	data = get_data(filters)
	columns = get_columns()
	return columns, data

def validate_filters(filters):
	if not filters.fiscal_year:
		frappe.throw(_("Fiscal Year {0} is required").format(filters.fiscal_year))

	fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
	if not fiscal_year:
		frappe.throw(_("Fiscal Year {0} does not exist").format(filters.fiscal_year))
	else:
		filters.year_start_date = getdate(fiscal_year.year_start_date)
		filters.year_end_date = getdate(fiscal_year.year_end_date)

	if not filters.from_date:
		filters.from_date = filters.year_start_date

	if not filters.to_date:
		filters.to_date = filters.year_end_date

	filters.from_date = getdate(filters.from_date)
	filters.to_date = getdate(filters.to_date)

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date cannot be greater than To Date"))

	if (filters.from_date < filters.year_start_date) or (filters.from_date > filters.year_end_date):
		frappe.msgprint(_("From Date should be within the Fiscal Year. Assuming From Date = {0}")\
			.format(formatdate(filters.year_start_date)))

		filters.from_date = filters.year_start_date

	if (filters.to_date < filters.year_start_date) or (filters.to_date > filters.year_end_date):
		frappe.msgprint(_("To Date should be within the Fiscal Year. Assuming To Date = {0}")\
			.format(formatdate(filters.year_end_date)))
		filters.to_date = filters.year_end_date

def get_data(filters):
	if filters.account:
		selected_account = frappe.db.sql("""select name, account_name, lft, rgt
		from `tabAccount` where company='{0}' and name = '{1}' order by lft""".format(filters.company, filters.account), as_dict=True)

		if selected_account:
			if selected_account[0].rgt - selected_account[0].lft > 1 :
				accounts = frappe.db.sql("""select name, parent_account, account_name, root_type, report_type, lft, rgt
					from `tabAccount` where company='{0}' and lft >= {1} and rgt <= {2} order by lft""".format(filters.company, selected_account[0].lft, selected_account[0].rgt), as_dict=True)
			else:
				accounts = selected_account
		else:
			return None
	else:
		accounts = frappe.db.sql("""select name, parent_account, account_name, root_type, report_type, lft, rgt
			from `tabAccount` where company='{0}' order by lft""".format(filters.company), as_dict=True)

	if not accounts:
		return None

	accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)
	account_condition = ""
	if filters.account:
		account_condition = " and name = '{0}'".format(filters.account)

	min_lft, max_rgt = frappe.db.sql("""select min(lft), max(rgt) from `tabAccount`
		where company=%s"""+account_condition, (filters.company,))[0]

	gl_entries_by_account = {}

	set_gl_entries_by_account(filters.company, filters.from_date,
		filters.to_date, min_lft, max_rgt, filters, gl_entries_by_account, ignore_closing_entries=not flt(filters.with_period_closing_entry))

	opening_balances = get_opening_balances(filters)

	total_row = calculate_values(accounts, gl_entries_by_account, opening_balances, filters)
	accumulate_values_into_parents(accounts, accounts_by_name, filters)

	data = prepare_data(accounts, filters, total_row, parent_children_map)
	data = filter_out_zero_value_rows(data, parent_children_map,
		show_zero_values=filters.get("show_zero_values"))

	return data

def get_opening_balances(filters):
	balance_sheet_opening = get_rootwise_opening_balances(filters, "Balance Sheet")
	pl_opening = get_rootwise_opening_balances(filters, "Profit and Loss")
	balance_sheet_opening.update(pl_opening)
	return balance_sheet_opening


def get_rootwise_opening_balances(filters, report_type):
	additional_conditions = ""
	if not filters.show_unclosed_fy_pl_balances:
		additional_conditions = " and posting_date >= %(year_start_date)s" \
			if report_type == "Profit and Loss" else ""

	if not flt(filters.with_period_closing_entry):
		additional_conditions += " and ifnull(voucher_type, '')!='Period Closing Voucher'"

	gle = frappe.db.sql("""
		select
			account, sum(debit) as opening_debit, sum(credit) as opening_credit
		from `tabGL Entry`
		where
			company=%(company)s
			{additional_conditions}
			and (posting_date < %(from_date)s or ifnull(is_opening, 'No') = 'Yes')
			and account in (select name from `tabAccount` where report_type=%(report_type)s)
		group by account""".format(additional_conditions=additional_conditions),
		{
			"company": filters.company,
			"from_date": filters.from_date,
			"report_type": report_type,
			"year_start_date": filters.year_start_date
		},
		as_dict=True)

	opening = frappe._dict()
	for d in gle:
		opening.setdefault(d.account, d)
	return opening

def calculate_values(accounts, gl_entries_by_account, opening_balances, filters):
	init = {
		"opening_debit": 0.0,
		"opening_credit": 0.0,
		"debit": 0.0,
		"credit": 0.0,
		"closing_debit": 0.0,
		"closing_credit": 0.0
	}

	total_row = {
		"account": None,
		"account_name": _("Total"),
		"warn_if_negative": True,
		"debit": 0.0,
		"credit": 0.0
	}

	for d in accounts:
		d.update(init.copy())

		# add opening
		d["opening_debit"] = opening_balances.get(d.name, {}).get("opening_debit", 0)
		d["opening_credit"] = opening_balances.get(d.name, {}).get("opening_credit", 0)
		for entry in gl_entries_by_account.get(d.name, []):
			if cstr(entry.is_opening) != "Yes":
				d["debit"] += flt(entry.debit)
				d["credit"] += flt(entry.credit)

		total_row["debit"] += d["debit"]
		total_row["credit"] += d["credit"]
	return total_row

def accumulate_values_into_parents(accounts, accounts_by_name, filters):
	for d in reversed(accounts):
		if d.parent_account:
			for key in value_fields:
				if d.parent_account not in accounts_by_name.keys():
					continue
				# frappe.throw(str(accounts_by_name[d.parent_account]["parent_account"]))
				# if selected_parent == accounts_by_name[d.parent_account]["parent_account"]:
				# if filters.account:
				# 	# frappe.throw(d.parent_account)
				# 	# frappe.throw(str(accounts_by_name[d.parent_account][key]))
				# 	frappe.throw(str(accounts_by_name))
				# 	accounts_by_name[d.parent_account][key] += d[key]
				accounts_by_name[d.parent_account][key] += d[key]

def prepare_data(accounts, filters, total_row, parent_children_map):
	selected_parent=frappe.get_value("Account", filters={"name": filters.account}, fieldname="parent_account")
	data = []
	company_currency = frappe.db.get_value("Company", filters.company, "default_currency")
	for d in accounts:
		has_value = False
		row = {
			"account_name": d.account_name,
			"account": d.name,
			# "parent_account": d.parent_account,
			"indent": d.indent,
			"from_date": filters.from_date,
			"to_date": filters.to_date,
			"currency": company_currency
		}
		if selected_parent != d.parent_account:
			row["parent_account"] = d.parent_account

		prepare_opening_and_closing(d)

		for key in value_fields:
			row[key] = flt(d.get(key, 0.0), 3)

			if abs(row[key]) >= 0.005:
				# ignore zero values
				has_value = True

		row["has_value"] = has_value
		data.append(row)

	data.extend([{},total_row])

	return data

def get_columns():
	return [
		{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 300
		},
		{
			"fieldname": "opening_debit",
			"label": (_("Opening") + " ("+ _("Dr")+")"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "opening_credit",
			"label": (_("Opening") + " ("+ _("Cr")+")"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "debit",
			"label": _("Debit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "credit",
			"label": _("Credit"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "closing_debit",
			"label": (_("Closing") + " ("+ _("Dr")+")"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "closing_credit",
			"label": (_("Closing") + " ("+ _("Cr")+")"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 120
		},
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"hidden": 1
		}
	]

def prepare_opening_and_closing(d):
	d["closing_debit"] = d["opening_debit"] + d["debit"]
	d["closing_credit"] = d["opening_credit"] + d["credit"]

	if d["closing_debit"] > d["closing_credit"]:
		d["closing_debit"] -= d["closing_credit"]
		d["closing_credit"] = 0.0

	else:
		d["closing_credit"] -= d["closing_debit"]
		d["closing_debit"] = 0.0

	if d["opening_debit"] > d["opening_credit"]:
		d["opening_debit"] -= d["opening_credit"]
		d["opening_credit"] = 0.0

	else:
		d["opening_credit"] -= d["opening_debit"]
		d["opening_debit"] = 0.0
