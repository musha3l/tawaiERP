# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
from frappe.utils import flt, getdate, formatdate, cstr

def execute(filters=None):
	validate_filters(filters)
	
	show_party_name = is_party_name_visible(filters)
	
	columns = get_columns(filters, show_party_name)
	data = get_data(filters, show_party_name)

	return columns, data
	
def get_data(filters, show_party_name):
	party_name_field = "customer_name" if filters.get("party_type")=="Customer" else "supplier_name" if filters.get("party_type")=="Supplier" else "employee_name"
	party_filters = {"name": filters.get("party")} if filters.get("party") else {}
	fields = ["name", party_name_field]
	if filters.get("party_type")=="Customer":
		fields.append("customer_group")

	elif filters.get("party_type")=="Supplier":
		fields.append("supplier_type")
	
	parties = frappe.get_all(filters.get("party_type"), fields = fields, 
		filters = party_filters, order_by="name")
	company_currency = frappe.db.get_value("Company", filters.company, "default_currency")
	opening_balances = get_opening_balances(filters)
	balances_within_period = get_balances_within_period(filters)
	
	data = []
	# total_debit, total_credit = 0, 0
	total_row = frappe._dict({
		"opening_debit": 0,
		"opening_credit": 0,
		"debit": 0,
		"credit": 0,
		"closing_debit": 0,
		"closing_credit": 0
	})
	for party in parties:
		row = { "party": party.name }
		if show_party_name:
			row["party_name"] = party.get(party_name_field)
		if filters.get("party_type")=="Customer":
			row["customer_group"] = party.get("customer_group")
		elif filters.get("party_type")=="Supplier":
			row["supplier_type"] = party.get("supplier_type")
		# opening
		opening_debit, opening_credit = opening_balances.get(party.name, [0, 0])
		row.update({
			"opening_debit": opening_debit,
			"opening_credit": opening_credit
		})
		
		# within period
		debit, credit = balances_within_period.get(party.name, [0, 0])
		row.update({
			"debit": debit,
			"credit": credit
		})
				
		# closing
		closing_debit, closing_credit = toggle_debit_credit(opening_debit + debit, opening_credit + credit)
		row.update({
			"closing_debit": closing_debit,
			"closing_credit": closing_credit
		})
		
		# totals
		for col in total_row:
			total_row[col] += row.get(col)
		
		row.update({
			"currency": company_currency
		})
		
		has_value = False
		if (opening_debit or opening_credit or debit or credit or closing_debit or closing_credit):
			has_value  =True
		
		if cint(filters.show_zero_values) or has_value:
			data.append(row)
		
	# Add total row
	
	total_row.update({
		"party": "'" + _("Totals") + "'",
		"currency": company_currency
	})
	data.append(total_row)
	
	return data
	
def get_opening_balances(filters):
	if filters.party_type=='Customer' and filters.party_group_or_type is not None:
		gle = frappe.db.sql("""
			select party, sum(debit) as opening_debit, sum(credit) as opening_credit 
			from `tabGL Entry`
			where company=%(company)s 
				and ifnull(party_type, '') = %(party_type)s and ifnull(party, '') != ''
				and (posting_date < %(from_date)s or ifnull(is_opening, 'No') = 'Yes')
				and party in (select name from `tabCustomer` where customer_group= %(party_group_or_type)s )
			group by party""", {
				"company": filters.company,
				"from_date": filters.from_date,
				"party_type": filters.party_type,
				"party_group_or_type": filters.party_group_or_type
			}, as_dict=True)
	elif filters.party_type=='Supplier' and filters.party_group_or_type is not None:
		gle = frappe.db.sql("""
			select party, sum(debit) as opening_debit, sum(credit) as opening_credit 
			from `tabGL Entry`
			where company=%(company)s 
				and ifnull(party_type, '') = %(party_type)s and ifnull(party, '') != ''
				and (posting_date < %(from_date)s or ifnull(is_opening, 'No') = 'Yes')
				and party in (select name from `tabSupplier` where supplier_type= %(party_group_or_type)s )
			group by party""", {
				"company": filters.company,
				"from_date": filters.from_date,
				"party_type": filters.party_type,
				"party_group_or_type": filters.party_group_or_type
			}, as_dict=True)
	else:
		gle = frappe.db.sql("""
			select party, sum(debit) as opening_debit, sum(credit) as opening_credit 
			from `tabGL Entry`
			where company=%(company)s 
				and ifnull(party_type, '') = %(party_type)s and ifnull(party, '') != ''
				and (posting_date < %(from_date)s or ifnull(is_opening, 'No') = 'Yes')
			group by party""", {
				"company": filters.company,
				"from_date": filters.from_date,
				"party_type": filters.party_type
			}, as_dict=True)
			
	opening = frappe._dict()
	for d in gle:
		opening_debit, opening_credit = toggle_debit_credit(d.opening_debit, d.opening_credit)
		opening.setdefault(d.party, [opening_debit, opening_credit])
		
	return opening
	
def get_balances_within_period(filters):
	if filters.party_type=='Customer' and filters.party_group_or_type is not None:
		gle = frappe.db.sql("""
			select party, sum(debit) as debit, sum(credit) as credit 
			from `tabGL Entry`
			where company=%(company)s 
				and ifnull(party_type, '') = %(party_type)s and ifnull(party, '') != ''
				and posting_date >= %(from_date)s and posting_date <= %(to_date)s 
				and ifnull(is_opening, 'No') = 'No'
				and party in (select name from `tabCustomer` where customer_group= %(party_group_or_type)s )
			group by party""", {
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date,
				"party_type": filters.party_type,
				"party_group_or_type": filters.party_group_or_type
			}, as_dict=True)
	elif filters.party_type=='Supplier' and filters.party_group_or_type is not None:
		gle = frappe.db.sql("""
			select party, sum(debit) as debit, sum(credit) as credit 
			from `tabGL Entry`
			where company=%(company)s 
				and ifnull(party_type, '') = %(party_type)s and ifnull(party, '') != ''
				and posting_date >= %(from_date)s and posting_date <= %(to_date)s 
				and ifnull(is_opening, 'No') = 'No'
				and party in (select name from `tabSupplier` where supplier_type= %(party_group_or_type)s )
			group by party""", {
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date,
				"party_type": filters.party_type,
				"party_group_or_type": filters.party_group_or_type
			}, as_dict=True)
	else:
		gle = frappe.db.sql("""
			select party, sum(debit) as debit, sum(credit) as credit 
			from `tabGL Entry`
			where company=%(company)s 
				and ifnull(party_type, '') = %(party_type)s and ifnull(party, '') != ''
				and posting_date >= %(from_date)s and posting_date <= %(to_date)s 
				and ifnull(is_opening, 'No') = 'No'
			group by party""", {
				"company": filters.company,
				"from_date": filters.from_date,
				"to_date": filters.to_date,
				"party_type": filters.party_type
			}, as_dict=True)


	balances_within_period = frappe._dict()
	for d in gle:
		balances_within_period.setdefault(d.party, [d.debit, d.credit])
		
	return balances_within_period
	
def toggle_debit_credit(debit, credit):
	if flt(debit) > flt(credit):
		debit = flt(debit) - flt(credit)
		credit = 0.0
	else:
		credit = flt(credit) - flt(debit)
		debit = 0.0
		
	return debit, credit
	
def get_columns(filters, show_party_name):
	columns = [
		{
			"fieldname": "party",
			"label": _(filters.party_type),
			"fieldtype": "Link",
			"options": filters.party_type,
			"width": 200
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
	
	if show_party_name:
		columns.insert(1, {
			"fieldname": "party_name",
			"label": _(filters.party_type) + " Name",
			"fieldtype": "Data",
			"width": 200
		})
	if filters.get("party_type")=="Customer":
		columns.insert(1, {
			"fieldname": "customer_group",
			"label": _("Customer Group"),
			"fieldtype": "Data",
			"width": 200
		})
	elif filters.get("party_type")=="Supplier":
		columns.insert(2, {
			"fieldname": "supplier_type",
			"label": _("Supplier Type"),
			"fieldtype": "Data",
			"width": 200
		})
	return columns
		
def is_party_name_visible(filters):
	show_party_name = False
	if filters.get("party_type") == "Customer":
		party_naming_by = frappe.db.get_single_value("Selling Settings", "cust_master_name")
	else:
		party_naming_by = frappe.db.get_single_value("Buying Settings", "supp_master_name")
		
	if party_naming_by == "Naming Series":
		show_party_name = True
		
	return show_party_name


def get_supplier_type(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(""" select name from `tabSupplier Type` """)


def get_customer_group(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(""" select name from `tabCustomer Group` """)



def validate_filters(filters):
	if filters.fiscal_year:
		fiscal_year = frappe.db.get_value("Fiscal Year", filters.fiscal_year, ["year_start_date", "year_end_date"], as_dict=True)
		if fiscal_year:
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

