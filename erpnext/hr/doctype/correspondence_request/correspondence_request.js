// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch('employee', 'department', 'department');

frappe.ui.form.on('Correspondence Request', {
	refresh: function(frm) {
		var table_data = frappe.render_template("correspondence_request",{"doc":frm.doc});
			$(frm.fields_dict["print_preview"].wrapper).html(table_data);
			refresh_field("print_preview");
	}
});
