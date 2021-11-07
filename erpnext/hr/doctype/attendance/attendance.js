// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
cur_frm.add_fetch('employee','department','department');
cur_frm.add_fetch('employee', 'company', 'company');
cur_frm.add_fetch('employee', 'employee_name', 'employee_name');

cur_frm.cscript.onload = function(doc, cdt, cdn) {
	if(doc.__islocal) cur_frm.set_value("attendance_date", frappe.datetime.get_today());
}
cur_frm.cscript.custom_employee = function(doc, cdt, cdn) {
	frappe.call({
				method: "get_attendance_hours",
				doc:doc,
				callback: function(r) {
						console.log(r.message);

			cur_frm.refresh_fields()
				}
			})
}

cur_frm.cscript.custom_b = function(doc, cdt, cdn) {
	frappe.call({
				method: "get_from_clock",
				doc:doc,
				callback: function(r) {
						console.log(r.message);
				}
			})
}

cur_frm.fields_dict.employee.get_query = function(doc,cdt,cdn) {
	return{
		query: "erpnext.controllers.queries.employee_query"
	}	
}
