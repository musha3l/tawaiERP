# Copyright (c) 2013, s and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = [
		{
			'fieldname': 'enquiry_type',
			'label': 'Type',
			'fieldtype': 'String'
		},
		{
			'fieldname': 'transaction_year',
			'label': 'Year',
			'fieldtype': 'Integer'
		},
		{
			'fieldname': 'transaction_date',
			'label': 'Date',
			'fieldtype': 'Date'
		},
		{
			'fieldname': 'quarter',
			'label': 'Quarter',
			'fieldtype': 'String'
		},
		{
			'fieldname': 'customer_name',
			'label': 'Client',
			'fieldtype': 'String'
		},
		{
			'fieldname': 'cost',
			'fieldtype': 'Float',
			'label': 'Sum - Cost'
		},
		{
			'fieldname': 'selling_price',
			'fieldtype': 'Float',
			'label': 'Sum - Selling Price'
		},
		{
			'fieldname': 'profit',
			'fieldtype': 'Float',
			'label': 'Sum - Profit'
		},
		{
			'fieldname': 'margin',
			'fieldtype': 'Percent',
			'label': 'Average - Margin'
		},
		{
			'fieldname': 'markup',
			'fieldtype': 'Percent',
			'label': 'Average - Markup'
		},
		{
			'fieldname': 'status',
			'label': 'Status',
			'fieldtype': 'String'
		},
		{
			'fieldname': 'rate',
			'fieldtype': 'Percent',
			'label': 'Rate'
		},
		{
			'fieldname': 'owner',
			'label': 'Owner',
			'fieldtype': 'String'
		},

	]

	data = frappe.db.sql('''select enquiry_type as enquiry_type,
	YEAR(transaction_date) as transaction_year, transaction_date as transaction_date,
	quarter as quarter, 
	customer_name as customer_name, cost as cost, selling_price as selling_price,
		profit as profit, margin as margin, marckup as markup,
		status as status, lead_owner as owner from tabOpportunity''')

	return columns, data
