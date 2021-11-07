frappe.listview_settings['Leave Claim'] = {
	onload: function (listview) {
		var arr=[]
		frappe.route_options = {
			
		};

		frappe.call({
			method:"frappe.client.get_list",
			args:{
				doctype:"User Notification",		
				filters: {
					"target_doctype": 'Leave Claim',
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
