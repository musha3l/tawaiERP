// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Promotion and Merit', {
	refresh: function(frm) {

	},
	onload: function(frm) {
		$(".grid-add-row").hide();
	}
	
});


frappe.ui.form.on('Promotion and Merit Employee', {
    level_increase: function (frm, cdt, cdn) {
        var d = locals[cdt][cdn];

        if(d.level_increase>100){
			frappe.call({
	            "method": "validate_level_increase_value",
	            doc: cur_frm.doc,
	            callback: function (r) {
	                frappe.model.set_value(cdt, cdn, "level_increase", 0);
	                frappe.model.set_value(cdt, cdn, "new_grade", d.current_grade);
	                frappe.model.set_value(cdt, cdn, "new_level", d.current_level);
	                frappe.model.set_value(cdt, cdn, "new_base", d.current_base);
	                frappe.model.set_value(cdt, cdn, "new_total_package", d.current_total_package);
	            }
	        });
        }

        next_level=d.current_level
        if(d.level_increase && (d.level_increase+d.current_level)>100){
			frappe.call({
	            "method": "get_new_grade_level",
	            args: {
                    'current_level': d.current_level,
                    'total_level': d.level_increase+d.current_level,
                    'current_grade': d.current_grade,
                    'current_base': d.current_base
                },
	            doc: cur_frm.doc,
	            callback: function (r) {
	                if(r){
	                	balance_level = 0
	                    frappe.model.set_value(cdt, cdn, "new_grade", r.message[0]);
	                    frappe.model.set_value(cdt, cdn, "new_level", r.message[1]);
	                    frappe.model.set_value(cdt, cdn, "new_base", r.message[2]);

			            salary = r.message[2]
			            for(l=1;l<r.message[1] ;l++){
			                salary += (salary*0.01)
			            }
			            new_package = Math.ceil(salary)

	                    if(new_package>=d.current_total_package){
	                    	new_package = new_package
	                    }else{
	                    	salary = new_package
	                    	while(new_package<d.current_total_package){
	                    		salary += (salary*0.01)
	                    		balance_level++;
	                    		new_package = Math.ceil(salary)
	                    	}
	                    }
	                    frappe.model.set_value(cdt, cdn, "new_level", r.message[1]+balance_level);
	                    frappe.model.set_value(cdt, cdn, "new_total_package", new_package);
	                }
	            }
	        });
			
		}else{

			frappe.model.set_value(cdt, cdn, "new_grade", d.current_grade);
			frappe.model.set_value(cdt, cdn, "new_level", d.level_increase+d.current_level);
			frappe.model.set_value(cdt, cdn, "new_base", d.current_base);

			salary = d.new_base
            for(l=1;l<d.new_level ;l++){
                salary += (salary*0.01)
            }
            new_package = Math.ceil(salary)

			frappe.model.set_value(cdt, cdn, "new_total_package", new_package);
		}

    }


});
