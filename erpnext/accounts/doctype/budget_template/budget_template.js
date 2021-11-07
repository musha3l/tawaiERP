// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Budget Template', {
	onload: function(frm) {
	frm.set_query("account", "accounts", function() {
			return {
				filters: {
					company: frm.doc.company,
					report_type: "Profit and Loss",
					is_group: 0
				}
			}
		})
	}
	,
	
});
