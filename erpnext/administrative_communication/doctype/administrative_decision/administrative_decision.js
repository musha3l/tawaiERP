// Copyright (c) 2016, Erpdeveloper.team and contributors
// For license information, please see license.txt
// cur_frm.add_fetch('employee', 'branch', 'branch');
// cur_frm.add_fetch('employee', 'department', 'department');

frappe.ui.form.on('Administrative Decision', {
	refresh: function(frm) {

		frappe.call({
				method: "unallowed_actions",
				doc: frm.doc,
				freeze: true,
				callback: function(r) {
						if (r.message && frappe.session.user != "Administrator") {
								frm.page.clear_actions_menu();
						}
				}
		});


if (frm.doc.type == "Received Document" && frm.doc.docstatus == 1) {
		frm.add_custom_button(__("Print Barcode"), function () {
			var win = window.open('');
			win.document.write('<img src="' + frm.doc.barcode_img + '"style="width: 300px;" onload="window.print();window.close()"/>');
			win.focus();
    }).addClass("btn-primary");;
	}


	 if (frm.doc.type == "Received Document") {
		 document.querySelector("[data-fieldname='decision_content']").style.display = "none";
		 document.querySelector("[data-fieldname='remarks']").style.display = "block";



	 }

	 if (frm.doc.type == "Sent Document" || frm.doc.type == "Inside Document") {
		 document.querySelector("[data-fieldname='decision_content']").style.display = "block";
		 document.querySelector("[data-fieldname='remarks']").style.display = "none";



	 }
	 // cur_frm.refresh_field('issued_by');
	 // cur_frm.refresh_field('issued_by_name');
	 // cur_frm.refresh_field('issue_designation');

	 if (frm.doc.custom == 1) {
		 // document.querySelector("[data-fieldname='decision_content']").style.display = "block";
		 // document.querySelector("[data-fieldname='remarks']").style.display = "none";
		 cur_frm.set_df_property("destination_custom", "hidden", false);
		 cur_frm.set_df_property("destination_name", "hidden", false);



	 }
	 else {
		 cur_frm.set_df_property("destination_custom", "hidden", true);
		 cur_frm.set_df_property("destination_name", "hidden", true);
	 }


		if(frm.doc.__islocal && frm.doc.employee)
		{
			$('[data-fieldname="employee"] input').trigger("change");
		}
		if (frappe.get_doc("Administrative Board",{'user_id':frappe.user.name})){
			if(frappe.get_doc("Administrative Board",{'user_id':frappe.user.name}).decision != "Approve"){
			frm.add_custom_button(__("Approve"), function() {
				return frappe.call({
					doc: frm.doc,
					method: "change_administrative_board_decision",
					args: {
						decision:"Approve"
					},
					callback: function(r) {
						if(!r.exc && r.message) {
							console.log(r.message);
							location.reload();
						}
					}
				});
			});
			frm.add_custom_button(__("Hold"), function() {
				return frappe.call({
					doc: frm.doc,
					method: "change_administrative_board_decision",
					args: {
						decision:"Hold"
					},
					callback: function(r) {
						if(!r.exc && r.message) {
							console.log(r.message);
							location.reload();
						}
					}
				});
			});
			frm.add_custom_button(__("Reject"), function() {
				return frappe.call({
					doc: frm.doc,
					method: "change_administrative_board_decision",
					args: {
						decision:"Reject"
					},
					callback: function(r) {
						if(!r.exc && r.message) {
							console.log(r.message);
							location.reload();
						}
					}
				});

			});
		}
	}
	},
	onload: function(frm){

		cur_frm.set_query("employee", function() {
	                return {
	                    query: "erpnext.administrative_communication.doctype.administrative_decision.administrative_decision.get_emp",
	                    filters: [
	                        // ["Employee", "name", "!=", cur_frm.doc.employee],
	                    ]
	                };
	            });

							cur_frm.set_query("issued_by", function() {
					        return {
										"query": "erpnext.administrative_communication.doctype.administrative_decision.administrative_decision.get_emp_sign",
					            // "filters": {
					 						// 	 "name": ["in" , ["EMP/1002","EMP/1004","EMP/1008"]]
					            // }
					        };
					    });

	},
	// workflow_state: function (frm) {
	// 	let issued_by_approval = frm.doc.issued_by_approval + 1;
	// 	console.log("ww",issued_by_approval);
	// 	frm.set_value('issued_by_approval', issued_by_approval)
	// },
	type: function(frm) {
		if (frm.doc.type == "Received Document"){
			frm.set_value('naming_series', "IN-")
		}else if (frm.doc.type == "Sent Document"){
			frm.set_value('naming_series', "OUT-")
		}else if (frm.doc.type == "Inside Document"){
			frm.set_value('naming_series', "INSIDE-")
		}else{
			frm.set_value('naming_series', "AD-")
		}

		if (frm.doc.type == "Received Document") {
		// 	cur_frm.set_df_property("issued_by", "hidden", true);
		// 	cur_frm.set_df_property("issued_by_name","hidden", true);
		// 	cur_frm.set_df_property("issue_designation", "hidden", true);
			cur_frm.toggle_reqd("decision_content", false)
			cur_frm.set_df_property("decision_content", "hidden", true);
			// $("textarea[data-fieldname='decision_content']").hide();
			document.querySelector("[data-fieldname='decision_content']").style.display = "none";
			document.querySelector("[data-fieldname='remarks']").style.display = "block";



			// cur_frm.toggle_reqd("attach", true)

		//
		//
		}
		//
		if (frm.doc.type == "Sent Document" || frm.doc.type == "Inside Document") {
		// 	cur_frm.set_df_property("issued_by", "hidden", false);
		// 	cur_frm.set_df_property("issued_by_name","hidden", false);
		// 	cur_frm.set_df_property("issue_designation", "hidden", false);
			cur_frm.toggle_reqd("decision_content", true)
			document.querySelector("[data-fieldname='decision_content']").style.display = "block";
			document.querySelector("[data-fieldname='remarks']").style.display = "none";


		//
		}
		// cur_frm.refresh_field('issued_by');
		// cur_frm.refresh_field('issued_by_name');
		// cur_frm.refresh_field('issue_designation');
		cur_frm.refresh_field('decision_content');
		cur_frm.refresh_field('attach');


	},

	reply_required: function(frm) {
		if (frm.doc.reply_required == 1){
			cur_frm.toggle_reqd("deadline", true)
		}else{
			cur_frm.toggle_reqd("deadline", false)
		}
	},
	replied_document: function(frm) {
		if (frm.doc.replied_document == 1){
			cur_frm.toggle_reqd("replied_administrative_decision", true)
		}else{
			cur_frm.toggle_reqd("replied_administrative_decision", false)
		}
	}



});
cur_frm.cscript.onload_post_render = function(doc,cdt,cdn){
	if(doc.__islocal) {
		cur_frm.clear_table('administrative_board');
		cur_frm.refresh_fields(['administrative_board']);
	}
};
// cur_frm.fields_dict.employee.get_query = function(doc) {
// 	frappe.call({
// 		doc: frm.doc,
// 		method: "get_department_employees",
// 		callback: function(r) {
// 			if(!r.exc && r.message) {
// 				console.log(r.message);
// 				return{
// 					filters:[
// 						['department', '=', doc.department]
// 					]
// 				};
// 			}
// 		}
// 	});
// 	return{
// 		filters:[
// 			['department', '=', doc.department]
// 		]
// 	};
// };






// Generate Bar Code button

// frappe.ui.form.on("Administrative Decision", "refresh", function(frm) {
// 	if (frm.doc.docstatus == 1) {
//     frm.add_custom_button(__("Generate Barcode"), function() {
//         // When this button is clicked, do this
//
//         // we take Administrative Decision Transaction Number to create a barcode for it
//         var name = frm.doc.name;
//
//         // do something with these values, like an ajax request
//         // or call a server side frappe function using frappe.call
// 		frappe.call({
// 		    method: 'barcode_attach2',
// 		    doc: frm.doc,
// 		    args: {
// 		            'name':frm.doc.title ,
// 		    },
// 		    callback: function(r) {
// 		        if (!r.exc) {
// 		            // code snippet
//
// 		            if (r.message){
// 		            	cur_frm.set_value('barcode_img',String(r.message));
// 									console.log("r.message",r.message);
// 		            	cur_frm.refresh_field('barcode_img');
// 									cur_frm.save();
// 		            	console.log(' barcode updated ')
// 		            }
//
// 		        }
// 		    }
// 		});
//
//
//
//
//     });
// 		}
// });
