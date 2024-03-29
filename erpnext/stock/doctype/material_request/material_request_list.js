frappe.listview_settings['Material Request'] = {
	add_fields: ["material_request_type", "status", "per_ordered"],
	get_indicator: function(doc) {
		if(doc.status=="Stopped") {
			return [__("Stopped"), "red", "status,=,Stopped"];
		} else if(doc.docstatus==1 && flt(doc.per_ordered, 2) == 0.00) {
			return [__("Pending"), "orange", "per_ordered,=,0"];
		} else if(doc.docstatus==1 && flt(doc.per_ordered, 2) < 100) {
			return [__("Partially Ordered"), "orange", "per_ordered,<,100"];
		} else if(doc.docstatus==1 && flt(doc.per_ordered, 2) == 100) {
			if (doc.material_request_type == "Purchase") {
				return [__("Ordered"), "green", "per_ordered,=,100"];
			} else if (doc.material_request_type == "Material Transfer") {
				return [__("Transfered"), "green", "per_ordered,=,100"];
			} else if (doc.material_request_type == "Material Issue") {
				return [__("Issued"), "green", "per_ordered,=,100"];
			}
		}
	},
	onload: function (listview) {
		var arr=[]
		frappe.route_options = {
			
		};

		frappe.call({
			method:"frappe.client.get_list",
			args:{
				doctype:"User Notification",		
				filters: {
					"target_doctype": 'Material Request',
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
};
