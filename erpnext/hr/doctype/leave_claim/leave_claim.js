// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch('leave_application', 'employee', 'employee');
cur_frm.add_fetch('leave_application', 'department', 'department');

frappe.ui.form.on('Leave Claim', {
	refresh: function(frm) {
		frm.set_query("leave_application", function() {
            return {
                filters: [
	                ['status', '=', 'Approved'],
	                ['docstatus', '=', 1]
            	]
            };
        });
	}
});





frappe.ui.form.on('Leave Claim Days', {
    date: function (frm, cdt, cdn) {
    	dates=[]
        var row = locals[cdt][cdn];
        if(row.date<cur_frm.doc.from_date || row.date>cur_frm.doc.to_date){
        	
        	frappe.call({
                "method": "validate_claim_date",
                doc: cur_frm.doc,
                callback: function (r) {
                    frappe.model.set_value(cdt, cdn, "date", );
                }
            });

        }

        for (let i = 0; i < cur_frm.doc.leave_claim_days.length; i++) {
        	if(dates.indexOf(cur_frm.doc.leave_claim_days[i].date) >= 0){
        		frappe.call({
	                "method": "validate_exist_date",
	                args: {
	                    'date': cur_frm.doc.leave_claim_days[i].date,
	                },
	                doc: cur_frm.doc,
	                callback: function (r) {
	                    frappe.model.set_value(cdt, cdn, "date", );
	                }
            	});
        	}else{
        		dates.push(cur_frm.doc.leave_claim_days[i].date)
        	}
	    }


    }

});