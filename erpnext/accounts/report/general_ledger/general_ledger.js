// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["General Ledger"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"account",
			"label": __("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"get_query": function() {
				var company = frappe.query_report_filters_by_name.company.get_value();
				return {
					"doctype": "Account",
					"filters": {
						"company": company,
					}
				}
			}
		},
		{
			"fieldname":"voucher_no",
			"label": __("Voucher No"),
			"fieldtype": "Data",
		},
		{
			"fieldtype": "Break",
		},
		{
			"fieldname":"party_type",
			"label": __("Party Type"),
			"fieldtype": "Select",
			"options": ["", "Customer", "Supplier","Employee","Imprest Permanent","Imprest Temporary"],
			"default": ""
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "Dynamic Link",
			"get_options": function() {
				var party_type = frappe.query_report_filters_by_name.party_type.get_value();
				var party = frappe.query_report_filters_by_name.party.get_value();
				if(party && !party_type) {
					frappe.throw(__("Please select Party Type first"));
				}
				return party_type;
			}
		},
		{
	"fieldname":"party_name",
	"label": __("Supplier Name"),
	"fieldtype": "Data",
	// "hidden": 1
},
// 		{
// 	"fieldname":"party_name",
// 	"label": __("Supplier Name"),
// 	"fieldtype": "Dynamic Link",
// 	"get_options": function() {
// 		// var party_type = frappe.query_report.filters_by_name.party_type.get_value();
// 		var party = frappe.query_report_filters_by_name.party.get_value();
// 		var test = "";
// 		// party_input = $(".page-form").find('[data-fieldname="party"]').find('input');
// 		 frappe.call({
// 			method: 'frappe.client.get_value',
// 			args: {
// 				doctype: 'Supplier',
// 				filters: {
// 					'name': party,
// 				},
// 				fieldname: ['supplier_name']
// 			},
// 			callback: function (data) {
// 				// if (data.message.status == 'Open' || data.message.status == 'Overdue')
// 				// frappe.db.set_value('Task', data.message.name, 'status', 'Cancelled');
// 				console.log("test",data.message.supplier_name)
// 				test = data.message.supplier_name;
// 				console.log("test",test)
// 				return test
// 			}
// 		});
// 		console.log("test",test)
// 		// var t= frappe.db.sql("""select supplier_name from tabSupplier""")
// 		// console.log("test",t)
// 		return test;
// 	}
// },

		{
			"fieldname":"group_by_voucher",
			"label": __("Group by Voucher"),
			"fieldtype": "Check",
			"default": 1
		},
		{
			"fieldname":"group_by_account",
			"label": __("Group by Account"),
			"fieldtype": "Check",
		},
		{
			"fieldname":"letter_head",
			"label": __("Letter Head"),
			"fieldtype": "Link",
			"options": "Letter Head",
			"default": frappe.defaults.get_default("letter_head"),
		}
	]
}
