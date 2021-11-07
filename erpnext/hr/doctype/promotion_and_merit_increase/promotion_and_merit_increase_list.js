frappe.listview_settings['Promotion and Merit Increase'] = {
	onload: function (listview) {
		var arr=[]
		frappe.route_options = {
			
		};

		frappe.call({
			method:"frappe.client.get_list",
			args:{
				doctype:"User Notification",		
				filters: {
					"target_doctype": 'Promotion and Merit Increase',
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
