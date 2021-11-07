# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import formatdate, getdate, flt, add_days

def execute(filters=None):
	filters.day_before_from_date = add_days(filters.from_date, -1)
	columns, data = get_columns(filters), get_data(filters)
	return columns, data
	
def get_data(filters):
	data = []
	group_data = []
	
	asset_categories_groups = get_asset_categories_groups(filters)
	asset_categories = get_asset_categories(filters)
	assets = get_assets(filters)
	asset_costs = get_asset_costs(assets, filters)
	asset_depreciations = get_accumulated_depreciations(assets, filters)
	print("+++++++++++++++++++++++++++")
	print(asset_categories_groups)
	print("+++++++++++++++++++++++++++")


	#~ for asset_category_main in asset_categories_groups:
		#~ print("1-------------------------------------------")
		#~ print(asset_category_main)
		#~ for asset_category in asset_categories_groups.get(asset_category_main):
			#~ print("2---------------------")
			#~ print(asset_category)
			#~ try:
				#~ row = frappe._dict()
				#~ row.asset_category = asset_category
				#~ print("3--------------")
				#~ print(asset_costs.get(asset_category))
				#~ row.update(asset_costs.get(asset_category))

				#~ row.cost_as_on_to_date = (flt(row.cost_as_on_from_date) + flt(row.cost_of_new_purchase)
					#~ - flt(row.cost_of_sold_asset) - flt(row.cost_of_scrapped_asset))
					
				#~ row.update(asset_depreciations.get(asset_category))
				#~ row.accumulated_depreciation_as_on_to_date = (flt(row.accumulated_depreciation_as_on_from_date) + 
					#~ flt(row.depreciation_amount_during_the_period) - flt(row.depreciation_eliminated))
				
				#~ row.net_asset_value_as_on_from_date = (flt(row.cost_as_on_from_date) - 
					#~ flt(row.accumulated_depreciation_as_on_from_date))
				
				#~ row.net_asset_value_as_on_to_date = (flt(row.cost_as_on_to_date) - 
					#~ flt(row.accumulated_depreciation_as_on_to_date))
			
				#~ data.append(row)
			#~ except:
				#~ data.append([asset_category])
				#~ print("error")
			#~ print ("_________________________________________________________________\n\n\n")

	for asset_category_main in asset_categories_groups:
		print("1-------------------------------------------")
		print(asset_category_main)
		group_row = frappe._dict()
		for asset_category in asset_categories_groups.get(asset_category_main):
			print("2---------------------")
			print(asset_category)
			try:
				row = frappe._dict()
				row.asset_category = asset_category
				print("3--------------")
				print(asset_costs.get(asset_category))
				row.update(asset_costs.get(asset_category))

				row.cost_as_on_to_date = (flt(row.cost_as_on_from_date, precision=2) + flt(row.cost_of_new_purchase, precision=2)
					- flt(row.cost_of_sold_asset, precision=2) - flt(row.cost_of_scrapped_asset, precision=2))
					
				row.update(asset_depreciations.get(asset_category))
				row.accumulated_depreciation_as_on_to_date = (flt(row.accumulated_depreciation_as_on_from_date, precision=2) + 
					flt(row.depreciation_amount_during_the_period, precision=2) - flt(row.depreciation_eliminated_during_the_period, precision=2))
				
				row.net_asset_value_as_on_from_date = (flt(row.cost_as_on_from_date, precision=2) - 
					flt(row.accumulated_depreciation_as_on_from_date, precision=2))
				
				row.net_asset_value_as_on_to_date = (flt(row.cost_as_on_to_date, precision=2) - 
					flt(row.accumulated_depreciation_as_on_to_date, precision=2))
				
				data.append(row)
				group_row.asset_category = asset_category_main

				for k in row:
					if k in group_row and k!="asset_category":
						group_row[k] += flt(row[k], precision=2)
					else:
						if k!="asset_category":
							group_row[k] = flt(row[k], precision=2)
			
			except Exception as e: 
				print(e)
				print("error")
				
			print ("_________________________________________________________________\n\n\n")

		print("jjjjjjjjjjjjjjjjjjjjjj")
		print(group_row)
		print("jjjjjjjjjjjjjjjjjjjjjj")
		group_data.append(group_row)
			
	total_row = frappe._dict()	
	total_row.asset_category = _("Total")

	
	if filters.show_by_group ==1:
		for row in group_data:
			for k in row:
				if k in total_row and k!="asset_category":
					total_row[k] += flt(row[k], precision=2)
				else:
					if k!="asset_category":
						total_row[k] = flt(row[k], precision=2)
		group_data.append([])
		group_data.append(total_row)
		return group_data
	
	for row in data:
		for k in row:
			if k in total_row and k!="asset_category":
				total_row[k] += flt(row[k], precision=2)
				row[k] = "{:.2f}".format(flt(row[k], precision=2))
			else:
				if k!="asset_category":
					total_row[k] = flt(row[k], precision=2)
					row[k] = "{:.2f}".format(flt(row[k], precision=2))

			
	data.append([])
	data.append(total_row)
		
	return data
	
def get_asset_categories(filters):
	return frappe.db.sql_list("""
		select distinct asset_category from `tabAsset` 
		where docstatus=1 and company=%s and purchase_date <= %s
	""", (filters.company, filters.to_date))
	
def get_assets(filters):
	return frappe.db.sql("""
		select name, asset_category, purchase_date, gross_purchase_amount, disposal_date, status
		from `tabAsset` 
		where docstatus=1 and company=%s and purchase_date <= %s""", 
		(filters.company, filters.to_date), as_dict=1)

def get_conditions(filters):
	conditions = ""

	if filters.get("asset_category"):
		lft, rgt = frappe.db.get_value("Asset Category",filters.get("asset_category"),
				["lft", "rgt"])

		conditions += """ and name in (select name from `tabAsset Category`
			where lft >= {0} and rgt <= {1}
			order by lft asc ) """.format(lft, rgt)
	return conditions


def get_asset_categories_groups(filters):		
	result = frappe._dict()
	conditions = get_conditions(filters)
	main_cat =  frappe.db.sql_list("""
		select name from `tabAsset Category` 
		where is_group=1 and parent_asset_category is not null {0}
	""".format(conditions))
	for m_cat in main_cat:
		child_cats = frappe.db.sql_list("""select name from `tabAsset Category` 
		where parent_asset_category =%s and is_group=0""",(m_cat))
		if child_cats : 
			result.setdefault(m_cat,child_cats)
	return result
	
	
def get_asset_costs(assets, filters):
	asset_costs = frappe._dict()
	for d in assets:
		asset_costs.setdefault(d.asset_category, frappe._dict({
			"cost_as_on_from_date": 0,
			"cost_of_new_purchase": 0,
			"cost_of_sold_asset": 0,
			"cost_of_scrapped_asset": 0
		}))
		
		costs = asset_costs[d.asset_category]
		
		if getdate(d.purchase_date) < getdate(filters.from_date):
			if not d.disposal_date or getdate(d.disposal_date) >= getdate(filters.from_date):
				costs.cost_as_on_from_date += flt(d.gross_purchase_amount, precision=2)
		else:
			costs.cost_of_new_purchase += flt(d.gross_purchase_amount, precision=2)
			
		if d.disposal_date and getdate(d.disposal_date) >= getdate(filters.from_date) \
				and getdate(d.disposal_date) <= getdate(filters.to_date):
			if d.status == "Sold":
				costs.cost_of_sold_asset += flt(d.gross_purchase_amount, precision=2)
			elif d.status == "Scrapped":
				costs.cost_of_scrapped_asset += flt(d.gross_purchase_amount, precision=2)
			
	return asset_costs
	
def get_accumulated_depreciations(assets, filters):
	asset_depreciations = frappe._dict()
	for d in assets:
		asset = frappe.get_doc("Asset", d.name)
		
		asset_depreciations.setdefault(d.asset_category, frappe._dict({
			"accumulated_depreciation_as_on_from_date": asset.opening_accumulated_depreciation,
			"depreciation_amount_during_the_period": 0,
			"depreciation_eliminated_during_the_period": 0
		}))
		
		depr = asset_depreciations[d.asset_category]
		
		for schedule in asset.get("schedules"):
			if getdate(schedule.schedule_date) < getdate(filters.from_date):
				if not asset.disposal_date or getdate(asset.disposal_date) >= getdate(filters.from_date):
					depr.accumulated_depreciation_as_on_from_date += flt(schedule.depreciation_amount, precision=2)
			elif getdate(schedule.schedule_date) <= getdate(filters.to_date):
				depr.depreciation_amount_during_the_period += flt(schedule.depreciation_amount, precision=2)
				
				if asset.disposal_date and getdate(schedule.schedule_date) >= getdate(asset.disposal_date):
					depr.depreciation_eliminated_during_the_period += flt(schedule.accumulated_depreciation_amount, precision=2)
		
	return asset_depreciations
	
def get_columns(filters):
	return [
		{
			"label": _("Asset Category"),
			"fieldname": "asset_category",
			"fieldtype": "Link",
			"options": "Asset Category",
			"width": 120
		},
		{
			"label": _("Cost as on") + " " + formatdate(filters.day_before_from_date),
			"fieldname": "cost_as_on_from_date",
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"label": _("Cost of New Purchase"),
			"fieldname": "cost_of_new_purchase",
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"label": _("Cost of Sold Asset"),
			"fieldname": "cost_of_sold_asset",
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"label": _("Cost of Scrapped Asset"),
			"fieldname": "cost_of_scrapped_asset",
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"label": _("Cost as on") + " " + formatdate(filters.to_date),
			"fieldname": "cost_as_on_to_date",
			"fieldtype": "Currency",
			"width": 140
		},
		{
			"label": _("Accumulated Depreciation as on") + " " + formatdate(filters.day_before_from_date),
			"fieldname": "accumulated_depreciation_as_on_from_date",
			"fieldtype": "Currency",
			"width": 270
		},
		{
			"label": _("Depreciation Amount during the period"),
			"fieldname": "depreciation_amount_during_the_period",
			"fieldtype": "Currency",
			"width": 240
		},
		{
			"label": _("Depreciation Eliminated due to disposal of assets"),
			"fieldname": "depreciation_eliminated_during_the_period",
			"fieldtype": "Currency",
			"width": 300
		},
		{
			"label": _("Accumulated Depreciation as on") + " " + formatdate(filters.to_date),
			"fieldname": "accumulated_depreciation_as_on_to_date",
			"fieldtype": "Currency",
			"width": 270
		},
		{
			"label": _("Net Asset value as on") + " " + formatdate(filters.day_before_from_date),
			"fieldname": "net_asset_value_as_on_from_date",
			"fieldtype": "Currency",
			"width": 200
		},
		{
			"label": _("Net Asset value as on") + " " + formatdate(filters.to_date),
			"fieldname": "net_asset_value_as_on_to_date",
			"fieldtype": "Currency",
			"width": 200
		}
	]
