// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Vat Report"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.year_start(),
			// "reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			// "reqd": 1,
			"width": "60px"
		},
		{
	 	"fieldname":"vat_value",
	 	"label": __("VAT %"),
	 	"fieldtype": "Select",
	 	"options": ["","5", "15"]
	 },
		{
			"fieldname":"account",
			"label": __("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"get_query": function() {
				return {
					"doctype": "Account",
					"filters": {
						"name": ["in",["22290001-RECEIVABLE VAT -ضريبة قيمة مضافة قابلة للخصم - T 5% - T","22290001-RECEIVABLE VAT -ضريبة قيمة مضافة قابلة للخصم - T 15% - T","22290002-PAYABLE VAT - ضريبة قيمة مضافة مستحقة -T - 5%  - T","22290002-PAYABLE VAT - ضريبة قيمة مضافة مستحقة -T - 15% - T"]],
					}
				}
			}
		},
		{
		"fieldname":"filter_by_supplier",
		"label": __("Supplier Invoice Date"),
		"fieldtype": "Check",
		"default": 0
	},

	]
}
