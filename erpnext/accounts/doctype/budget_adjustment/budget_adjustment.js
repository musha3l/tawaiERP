// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Budget Adjustment', {
	onload: function(frm) {
		frm.set_query("target_budget", function() {
			return {
				filters: {
					docstatus: 1
				}
			}
		})
		
		frm.set_query("cost_center", function() {
			return {
				filters: {
					company: frm.doc.company
				}
			}
		})

		frm.set_query("project", function() {
			return {
				filters: {
					company: frm.doc.company
				}
			}
		})
		
		frm.set_query("account", "accounts", function() {
			return {
				filters: {
					company: frm.doc.company,
					report_type: "Profit and Loss",
					is_group: 0
				}
			}
		})
		
		frm.set_query("monthly_distribution", function() {
			return {
				filters: {
					fiscal_year: frm.doc.fiscal_year
				}
			}
		})
	},

	refresh: function(frm) {
		frm.trigger("toggle_reqd_fields")
	},

	budget_against: function(frm) {
		frm.trigger("set_null_value")
		frm.trigger("toggle_reqd_fields")
	},

	set_null_value: function(frm) {
		if(frm.doc.budget_against == 'Cost Center') {
			frm.set_value('project', null)
		} else {
			frm.set_value('cost_center', null)
		}
	},

	toggle_reqd_fields: function(frm) {
		frm.toggle_reqd("cost_center", frm.doc.budget_against=="Cost Center");
		frm.toggle_reqd("project", frm.doc.budget_against=="Project");
	}
});

cur_frm.cscript.budget_template = function(doc, dt, dn) {
	doc.goals = [];
	cur_frm.clear_table("accounts")
	cur_frm.refresh_field("accounts")

	erpnext.utils.map_current_doc({
		method: "erpnext.accounts.doctype.budget.budget.fetch_budget_template",
		source_name: cur_frm.doc.budget_template,
		frm: cur_frm
	});
}

cur_frm.cscript.target_budget = function(doc, dt, dn) {
	doc.goals = [];
	cur_frm.clear_table("accounts")
	cur_frm.refresh_field("accounts")

	erpnext.utils.map_current_doc({
		method: "erpnext.accounts.doctype.budget_adjustment.budget_adjustment.fetch_budget",
		source_name: cur_frm.doc.target_budget,
		frm: cur_frm
	});
}

