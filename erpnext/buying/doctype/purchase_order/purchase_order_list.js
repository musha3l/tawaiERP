frappe.listview_settings['Purchase Order'] = {
	add_fields: ["base_grand_total", "company", "currency", "supplier",
		"supplier_name", "per_received", "per_billed", "status"],
	get_indicator: function(doc) {
        if(doc.status==="Closed"){
			return [__("Closed"), "green", "status,=,Closed"];
		} else if (doc.status==="Delivered") {
			return [__("Delivered"), "green", "status,=,Closed"];
		}else if(flt(doc.per_received, 2) < 100 && doc.status!=="Closed") {
			if(flt(doc.per_billed, 2) < 100) {
				return [__("To Receive and Bill"), "orange",
					"per_received,<,100|per_billed,<,100|status,!=,Closed"];
			} else {
				return [__("To Receive"), "orange",
					"per_received,<,100|per_billed,=,100|status,!=,Closed"];
			}
		} else if(flt(doc.per_received, 2) == 100 && flt(doc.per_billed, 2) < 100 && doc.status!=="Closed") {
			return [__("To Bill"), "orange", "per_received,=,100|per_billed,<,100|status,!=,Closed"];
		} else if(flt(doc.per_received, 2) == 100 && flt(doc.per_billed, 2) == 100 && doc.status!=="Closed") {
			return [__("Completed"), "green", "per_received,=,100|per_billed,=,100|status,!=,Closed"];
		}
	},
	onload: function (listview) {

		var method = "erpnext.buying.doctype.purchase_order.purchase_order.close_or_unclose_purchase_orders";

		listview.page.add_menu_item(__("Close"), function() {
			listview.call_for_selected_items(method, {"status": "Closed"});
		});

		listview.page.add_menu_item(__("Re-open"), function() {
			listview.call_for_selected_items(method, {"status": "Submitted"});
		});

		
		var arr=[]
		frappe.route_options = {
			
		};

		frappe.call({
			method:"frappe.client.get_list",
			args:{
				doctype:"User Notification",		
				filters: {
					"target_doctype": 'Purchase Order',
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
	// onload: function(listview) {
	// 	var method = "erpnext.buying.doctype.purchase_order.purchase_order.close_or_unclose_purchase_orders";

	// 	listview.page.add_menu_item(__("Close"), function() {
	// 		listview.call_for_selected_items(method, {"status": "Closed"});
	// 	});

	// 	listview.page.add_menu_item(__("Re-open"), function() {
	// 		listview.call_for_selected_items(method, {"status": "Submitted"});
	// 	});
	// }
};
