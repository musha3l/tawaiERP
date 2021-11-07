// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Delegation', {
	refresh: function(frm) {

		if (!frm.doc.__islocal && cur_frm.doc.docstatus == 1) {
				cur_frm.toggle_display("html_0", true);
				var table_data = frappe.render_template("delegation", { "doc": frm.doc });
				$(frm.fields_dict["html_0"].wrapper).html(table_data);
				refresh_field("html_0");
		}

	}
});
