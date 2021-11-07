// frappe.listview_settings['Leave Application'] = {
// 	add_fields: ["status", "from_date", "to_date","leave_type", "employee", "employee_name", "total_leave_days"],
// 	filters:[["status","!=", "Rejected"]],
// 	get_indicator: function(doc) {
// 		return [__(doc.status),frappe.utils.guess_colour(doc.status),
// 			"status,=," + doc.status];
// 	}
// 	}
frappe.listview_settings['Leave Application'] = {
	colwidths: {"employee_name": 1,"leave_type": 1,"status": 1,"from_date": 1,"employee_name": 1},
	add_fields: ["status", "from_date", "to_date","leave_type", "employee_name"],
	filters:[["status","!=", "Rejected"]],
	// get_indicator: function(doc) {
	// 	return [__(doc.status),frappe.utils.guess_colour(doc.status),
	// 		"status,=," + doc.status];
	// },
	onload: function (listview) {
		var arr=[]
		frappe.route_options = {

		};

		frappe.call({
			method:"frappe.client.get_list",
			args:{
				doctype:"User Notification",
				filters: {
					"target_doctype": 'Leave Application',
					"status": 'Active',
					"user": frappe.user.name
				},
				fields: "target_docname",
			},
			callback: function(r) {
				for(var i=0;i<r.message.length;i++){
					arr.push(r.message[i].target_docname)
				}
				frappe.route_options = {
					"name": ["in", arr]
				};
			}
		});

	}
}

frappe.get_indicator = function(doc, doctype) {
	// console.log(doc.workflow_state);
if (doc.workflow_state) {
		if (doc.workflow_state === "Approved By HR Specialist (F.T)" || doc.workflow_state === "Approved By CEO (+30)"  || doc.workflow_state === "Approved By HR Manager" || doc.workflow_state === "Approved By Director (F.T)" ) {
				return [__(doc.workflow_state), "green", "workflow_state,=," + doc.workflow_state]
		}
		 else if ((doc.workflow_state.includes('Rejected')) || (doc.workflow_state.includes('Canceled'))) {
			 return [__(doc.workflow_state), "red", "workflow_state,=," + doc.workflow_state]
		}
		else {
			return [__(doc.workflow_state), "darkgrey", "workflow_state,=," + doc.workflow_state]
		}
}
else if (doc.doctype == "Loan Type") {
	if (doc.disabled == 1) {
		return [__("Disabled"), "darkgrey", "disabled,=," + 1]
	}

	if (doc.disabled == 0) {
		return [__("Enabled"), "blue", "disabled,=," + 0]
	}

}
else if (doc.status) {
		return [__(doc.status),frappe.utils.guess_colour(doc.status),
			"status,=," + doc.status];
}
else {
	if(doc.docstatus==0) {
		return [__("Draft"), "red", "docstatus,=," + 0]

	} else if(doc.docstatus==2) {
		return [__("Cancelled"), "grey", "docstatus,=," + 2]
	} else {
		return [__("Submitted"), "blue", "docstatus,=," + 1]
	}
}
// else {
//  location.reload();
// }
}
