// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Upload Journal Entry', {
	refresh: function(frm) {
		if (cur_frm.doc.je == null){
			cur_frm.set_df_property("load_data", "hidden", 0)
		}
		else {
			cur_frm.set_df_property("load_data", "hidden", 1)
		}
console.log("tt");
},
	get_template:function() {
		window.open("/files/Journal_Entry_template8b10a5.xls", "_blank");

		// frappe.call({
		// 		method: "erpnext.accounts.doctype.upload_journal_entry.upload_journal_entry.get_template",
		// 		callback: function (r) {
		// 				if(r.message){
		// 						console.log(r.message)
		// 				}
		// 		}
		// });
	},
	load_data: function (frm) {
		frappe.call({
			doc: frm.doc,
			method: 'load_file',
			args: {
			},
			callback: function (value) {
				console.log(value)
				refresh_field("je");
				cur_frm.set_df_property("load_data", "hidden", 1)
				refresh_field("load_data");
				frm.save();

			}
		})
	}
});
