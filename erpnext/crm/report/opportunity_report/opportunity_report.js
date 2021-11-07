// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Opportunity Report"] = {
	"filters": [
	{
		"fieldname":"status",
		"label": __("Status"),
		"fieldtype": "Select",
		"options": ["Open","Closed"],
		"default": ""
	},
	{
		"fieldname":"type",
		"label": __("Type"),
		"fieldtype": "Select",
		"options": ["Sales","Maintenance"],
		"default": ""
	},
	{
		"fieldname":"owner",
		"label": __("Owner"),
		"fieldtype": "Link",
		"options": "User",
		"default": ""
	},
	{
		"fieldname":"quarter",
		"label": __("Quarter"),
		"fieldtype": "Link",
		"options": "Quarter",
		"default": ""
	},
			
	]
}
