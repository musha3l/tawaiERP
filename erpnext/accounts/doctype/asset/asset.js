// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.provide("erpnext.asset");
cur_frm.add_fetch("company", "asset_received_but_not_billed", "credit_to");

frappe.ui.form.on('Asset', {
	onload: function(frm) {
		frm.set_query("item_code", function() {
			return {
				"filters": {
					"disabled": 0,
					"is_fixed_asset": 1,
					"is_stock_item": 0
				}
			};
		});

		frm.set_query("warehouse", function() {
			return {
				"filters": {
					"company": frm.doc.company,
					"is_group": 0
				}
			};
		});
	},

	refresh: function(frm) {
		frm.events.show_general_ledger(frm);
		cur_frm.cscript.item_code = function(doc, cdt, cdn) {
			frm.set_value('asset_name',frm.doc.barcode);
			refresh_field('asset_name');

		}
		frappe.ui.form.trigger("Asset", "is_existing_asset");
		frm.toggle_display("next_depreciation_date", frm.doc.docstatus < 1);
		frm.events.make_schedules_editable(frm);

		if (frm.doc.docstatus==1) {
			if (frm.doc.status=='Submitted' && !frm.doc.is_existing_asset && !frm.doc.purchase_invoice) {
				frm.add_custom_button("Make Purchase Invoice", function() {
					erpnext.asset.make_purchase_invoice(frm);
				});
			}
			if (in_list(["Submitted", "Partially Depreciated", "Fully Depreciated"], frm.doc.status)) {
				frm.add_custom_button("Transfer Asset", function() {
					erpnext.asset.transfer_asset(frm);
				});

				frm.add_custom_button("Set Employee", function() {
					erpnext.asset.set_employee(frm);
				});

				frm.add_custom_button("Scrap Asset", function() {
					erpnext.asset.scrap_asset(frm);
				});

				frm.add_custom_button("Sale Asset", function() {
					erpnext.asset.make_sales_invoice(frm);
				});

			} else if (frm.doc.status=='Scrapped') {
				frm.add_custom_button("Restore Asset", function() {
					erpnext.asset.restore_asset(frm);
				});
			}

			frm.trigger("show_graph");
		}
	},
	show_general_ledger: function(frm) {
		if(frm.doc.docstatus==1) {
			frm.add_custom_button(__('Ledger'), function() {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.posting_date,
					"to_date": frm.doc.posting_date,
					"company": frm.doc.company,
					group_by_voucher: 0
				};
				frappe.set_route("query-report", "General Ledger");
			}, "fa fa-table");
		}
	},
	show_graph: function(frm) {
		var x_intervals = ["x", frm.doc.purchase_date];
		var asset_values = ["Asset Value", frm.doc.gross_purchase_amount];
		var last_depreciation_date = frm.doc.purchase_date;

		if(frm.doc.opening_accumulated_depreciation) {
			last_depreciation_date = frappe.datetime.add_months(frm.doc.next_depreciation_date,
				-1*frm.doc.frequency_of_depreciation);

			x_intervals.push(last_depreciation_date);
			asset_values.push(flt(frm.doc.gross_purchase_amount) -
				flt(frm.doc.opening_accumulated_depreciation));
		}

		$.each(frm.doc.schedules || [], function(i, v) {
			x_intervals.push(v.schedule_date);
			asset_value = flt(frm.doc.gross_purchase_amount) - flt(v.accumulated_depreciation_amount);
			if(v.journal_entry) {
				last_depreciation_date = v.schedule_date;
				asset_values.push(asset_value)
			} else {
				if (in_list(["Scrapped", "Sold"], frm.doc.status)) {
	 				asset_values.push(null)
				} else {
					asset_values.push(asset_value)
				}
			}
		})

		if(in_list(["Scrapped", "Sold"], frm.doc.status)) {
			x_intervals.push(frm.doc.disposal_date);
			asset_values.push(0);
			last_depreciation_date = frm.doc.disposal_date;
		}

		frm.dashboard.setup_chart({
			data: {
				x: 'x',
				columns: [x_intervals, asset_values],
				regions: {
					'Asset Value': [{'start': last_depreciation_date, 'style':'dashed'}]
				}
			},
			legend: {
				show: false
			},
			axis: {
				x: {
					type: 'timeseries',
					tick: {
						format: "%d-%m-%Y"
					}
				},
				y: {
					min: 0,
					padding: {bottom: 10}
				}
			}
		});
	},

	item_code: function(frm) {
		if(frm.doc.item_code) {
			frappe.call({
				method: "erpnext.accounts.doctype.asset.asset.get_item_details_with_company",
				args: {
					item_code: frm.doc.item_code,
					company: frm.doc.company
				},
				callback: function(r, rt) {
					if(r.message) {
						$.each(r.message, function(field, value) {
							frm.set_value(field, value);
						})
					}
				}
			})
		}
	},

	is_existing_asset: function(frm) {
		frm.toggle_enable("supplier", frm.doc.is_existing_asset);
		frm.toggle_reqd("next_depreciation_date", !frm.doc.is_existing_asset);
	},

	opening_accumulated_depreciation: function(frm) {
		erpnext.asset.set_accululated_depreciation(frm);
	},

	depreciation_method: function(frm) {
		frm.events.make_schedules_editable(frm);
	},

	make_schedules_editable: function(frm) {
		var is_editable = frm.doc.depreciation_method==="Manual" ? true : false;
		frm.toggle_enable("schedules", is_editable);
		frm.fields_dict["schedules"].grid.toggle_enable("schedule_date", is_editable);
		frm.fields_dict["schedules"].grid.toggle_enable("depreciation_amount", is_editable);
	}

});

frappe.ui.form.on('Depreciation Schedule', {
	make_depreciation_entry: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (!row.journal_entry) {
			frappe.call({
				method: "erpnext.accounts.doctype.asset.depreciation.make_depreciation_entry",
				args: {
					"asset_name": frm.doc.name,
					"date": row.schedule_date
				},
				callback: function(r) {
					frappe.model.sync(r.message);
					frm.refresh();
				}
			})
		}
	},

	depreciation_amount: function(frm, cdt, cdn) {
		erpnext.asset.set_accululated_depreciation(frm);
	}

})

erpnext.asset.set_accululated_depreciation = function(frm) {
	if(frm.doc.depreciation_method != "Manual") return;

	accumulated_depreciation = flt(frm.doc.opening_accumulated_depreciation);
	$.each(frm.doc.schedules || [], function(i, row) {
		accumulated_depreciation  += flt(row.depreciation_amount);
		frappe.model.set_value(row.doctype, row.name,
			"accumulated_depreciation_amount", accumulated_depreciation);
	})
}

erpnext.asset.make_purchase_invoice = function(frm) {
	frappe.call({
		args: {
			"asset": frm.doc.name,
			"item_code": frm.doc.item_code,
			"gross_purchase_amount": frm.doc.gross_purchase_amount,
			"company": frm.doc.company,
			"posting_date": frm.doc.purchase_date
		},
		method: "erpnext.accounts.doctype.asset.asset.make_purchase_invoice",
		callback: function(r) {
			var doclist = frappe.model.sync(r.message);
			frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
		}
	})
}

erpnext.asset.make_sales_invoice = function(frm) {
	frappe.call({
		args: {
			"asset": frm.doc.name,
			"item_code": frm.doc.item_code,
			"company": frm.doc.company
		},
		method: "erpnext.accounts.doctype.asset.asset.make_sales_invoice",
		callback: function(r) {
			var doclist = frappe.model.sync(r.message);
			frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
		}
	})
}

erpnext.asset.scrap_asset = function(frm) {
	var d = new frappe.ui.Dialog({
    'fields': [
        {'fieldname': 'ht', 'fieldtype': 'HTML'},
        {'label':__("Posting Date"),'fieldname': 'posting_date', 'fieldtype': 'Date', 'default': frappe.datetime.nowdate()}
    ],
		primary_action: function(){
			d.hide();
			var data = d.get_values();
			frappe.call({
				args: {
					"asset_name": frm.doc.name,
					"posting_date":data.posting_date
				},
				method: "erpnext.accounts.doctype.asset.depreciation.scrap_asset",
				callback: function(r) {
					cur_frm.reload_doc();
				}
			})
		}
	});
	d.fields_dict.ht.$wrapper.html(__("Do you really want to scrap this asset?"));
	d.show();
}

erpnext.asset.set_employee = function(frm) {

	var d = new frappe.ui.Dialog({
    'fields': [
        {'fieldname': 'ht', 'fieldtype': 'HTML'},
				{
				"label": __("Employee"),
				"fieldname": "target_empoyee",
				"fieldtype": "Link",
				"options": "Employee",
				"default": frm.doc.employee,
				"get_query": "erpnext.controllers.queries.employee_query"
			},

	],
		primary_action: function(){
			d.hide();
			var data = d.get_values();
			frappe.call({
				args: {
					"asset_name": frm.doc.name,
					"employee":data.target_empoyee
				},
				method: "erpnext.accounts.doctype.asset.depreciation.set_employee",
				callback: function(r) {
					cur_frm.reload_doc();
				}
			})
		}
	});
	d.fields_dict.ht.$wrapper.html(__("Assign Employee to Asset"));
	d.show();

}

erpnext.asset.restore_asset = function(frm) {
	frappe.confirm(__("Do you really want to restore this scrapped asset?"), function () {
		frappe.call({
			args: {
				"asset_name": frm.doc.name
			},
			method: "erpnext.accounts.doctype.asset.depreciation.restore_asset",
			callback: function(r) {

				cur_frm.reload_doc();
			}
		})
	})
}

erpnext.asset.transfer_asset = function(frm) {
	var dialog = new frappe.ui.Dialog({
		title: __("Transfer Asset"),
		fields: [
			{
				"label": __("Target Warehouse"),
				"fieldname": "target_warehouse",
				"fieldtype": "Link",
				"options": "Warehouse",
				"default": frm.doc.warehouse,
				"get_query": function () {
					return {
						filters: [
							["Warehouse", "company", "in", ["", cstr(frm.doc.company)]],
							["Warehouse", "is_group", "=", 0]
						]
					}
				},
				"reqd": 0
			},
			{
				"label": __("Target Cost Center"),
				"fieldname": "target_cost_center",
				"fieldtype": "Link",
				"options": "Cost Center",
				"default": frm.doc.depreciation_cost_center,
				"onchange": function(e) {
					$('input[data-fieldname="target_project"]').val(null);
				},
				"get_query": function () {
					return {
						filters: [
							["Cost Center", "is_group", "=", 0],
							["Cost Center", "is_active", "=", 1]
						]
					}
				}
			},
			{
				"label": __("Target Project"),
				"fieldname": "target_project",
				"fieldtype": "Link",
				"onchange": function(e) {
					$('input[data-fieldname="target_cost_center"]').val(null);
				},
				"options": "Project",
				"default": frm.doc.project
			},
			{
				"label": __("Date"),
				"fieldname": "transfer_date",
				"fieldtype": "Datetime",
				"reqd": 1,
				"default": frappe.datetime.now_datetime()
			}
		]
	});

	dialog.set_primary_action(__("Transfer"), function() {
		args = dialog.get_values();
		if(!args) return;
		dialog.hide();
		return frappe.call({
			type: "GET",
			method: "erpnext.accounts.doctype.asset.asset.transfer_asset",
			args: {
				args: {
					"asset": frm.doc.name,
					"transaction_date": args.transfer_date,
					"source_warehouse": frm.doc.warehouse,
					"target_warehouse": args.target_warehouse,
					"cost_center": args.target_cost_center,
					"project": args.target_project,
					"company": frm.doc.company
				}
			},
			freeze: true,
			callback: function(r) {
				cur_frm.reload_doc();
			}
		})
	});
	dialog.show();
}


// Generate Bar Code button

frappe.ui.form.on("Asset", "refresh", function(frm) {
    frm.add_custom_button(__("Generate Barcode"), function() {
        // When this button is clicked, do this

        // we take asset name to create a barcode for it
        var name = frm.doc.name;

        // do something with these values, like an ajax request
        // or call a server side frappe function using frappe.call
		frappe.call({
		    method: 'barcode_attach2',
		    doc: frm.doc,
		    args: {
		            'name':name ,
		    },
		    callback: function(r) {
		        if (!r.exc) {
		            // code snippet

		            if (r.message){
		            	cur_frm.set_value('barcode_img',String(r.message));

		            	cur_frm.refresh_field('barcode_img');
		            	console.log(' barcode updated ')
		            }

		        }
		    }
		});




    });
});
