// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Asset Report"] = {
	"filters": [
		{
			"fieldname":"asset_category",
			"label": __("Asset Category"),
			"fieldtype": "Link",
			"options": "Asset Category"
		},
		{
			"fieldname":"total_only",
			"label": __("Show Group Total Only"),
			"fieldtype": "Check",
			"default": 0
		},
		{
			"fieldname":"date_filter",
			"label": __("Date Filter"),
			"fieldtype": "Select",
			"options":["Purchase Date","Next Depreciation Date"],
			"default": "Purchase Date"
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": ""
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": ""
		},
		
	]
}
