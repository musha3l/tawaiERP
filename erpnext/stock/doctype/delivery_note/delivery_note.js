// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

{% include 'erpnext/selling/sales_common.js' %};

frappe.provide("erpnext.stock");
frappe.provide("erpnext.stock.delivery_note");


frappe.ui.form.on("Delivery Note", {
	refresh: function(frm,cdt,cdn){
		// cur_frm.fields_dict["items"].grid.set_column_disp(["price_list_rate","discount_and_margin","section_break_1","section_break_25","billed_amt"]);
		// cur_frm.fields_dict["taxes"].grid.set_column_disp(["section_break_8","section_break_9"]);
		// cur_frm.toggle_display(["section_break_31","section_break_44","section_break_49","totals","sales_team_section_break","currency_and_price_list","taxes_section","section_break_41","items_section"], false);
	},
	project: function(frm,cdt,cdn){
		if (frm.doc.project && frm.doc.project != "" ){
		frm.script_manager.trigger("customer");
		}
	},
	customer: function(frm){
		if (frm.doc.project && frm.doc.project != "" ){
			frm.add_fetch("project", "customer", "customer");
		}
		if(frm.doc.customer && frm.doc.customer != ""){
			var name = frappe.call({
				method:"frappe.client.get_value",
				args: {
				doctype:"Customer",
				filters: {
					customer_name:frm.doc.customer,
				},
				fieldname:["customer_name_in_arabic"]
				}, 
				callback: function(r) { 
				console.log(r);
	
				// set the returned value in a field
				cur_frm.set_value("customer_name_in_arabic", "");
				if(r.message){
				cur_frm.set_value("customer_name_in_arabic", r.message["customer_name_in_arabic"]);
	}
				}
			})
		}
		

	},
	setup: function(frm) {
		frm.custom_make_buttons = {
			'Packing Slip': 'Packing Slip',
			'Installation Note': 'Installation Note',
			'Sales Invoice': 'Invoice',
			'Stock Entry': 'Return',
		},
		frm.set_indicator_formatter('item_code',
			function(doc) {
				return (doc.docstatus==1 || doc.qty<=doc.actual_qty) ? "green" : "orange"
			})

		frm.set_query("warehouse", "items", function() {
			return {
				filters: [
					["Warehouse", "company", "in", ["", cstr(frm.doc.company)]],
					["Warehouse", "is_group", "=", 0]
				]
			}
		})

	}
});
var map_current_doc_new = function(opts) {
	console.log(opts);
	console.log("query filters: ")
	console.log(opts.get_query_filters)
	// if(cur_dialog && cur_dialog.fields_dict.customer.value){
	// 	opts.setters["customer"] = cur_dialog.fields_dict.customer.value || ""
	// 	console.log("Setter Worked")
	// }else{
	// 	console.log("Setter Failed")
	// }
	if(opts.get_query_filters) {
		opts.get_query = function() {
			console.log("@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
			console.log(opts.get_query_filters)
			console.log(opts)
			opts.get_query_filters["transaction_date"] = undefined;
			if(cur_dialog && cur_dialog.fields_dict.date_range.value){
				opts.get_query_filters["delivery_date"] = cur_dialog.fields_dict.date_range.value
			}
			return {filters: opts.get_query_filters};
		}
	}
	var _map = function() {
		if($.isArray(cur_frm.doc.items) && cur_frm.doc.items.length > 0) {
			// remove first item row if empty
			if(!cur_frm.doc.items[0].item_code) {
				cur_frm.doc.items = cur_frm.doc.items.splice(1);
			}

			// find the doctype of the items table
			var items_doctype = frappe.meta.get_docfield(cur_frm.doctype, 'items').options;

			// find the link fieldname from items table for the given
			// source_doctype
			var link_fieldname = null;
			frappe.get_meta(items_doctype).fields.forEach(function(d) {
				if(d.options===opts.source_doctype) link_fieldname = d.fieldname; });

			// search in existing items if the source_name is already set and full qty fetched
			var already_set = false;
			var item_qty_map = {};

			$.each(cur_frm.doc.items, function(i, d) {
				opts.source_name.forEach(function(src) {
					if(d[link_fieldname]==src) {
						already_set = true;
						if (item_qty_map[d.scope_item])
							item_qty_map[d.scope_item] += flt(d.qty);
						else
							item_qty_map[d.scope_item] = flt(d.qty);
					}
				});
			});

			if(already_set) {
				opts.source_name.forEach(function(src) {
					frappe.model.with_doc(opts.source_doctype, src, function(r) {
						var source_doc = frappe.model.get_doc(opts.source_doctype, src);
						$.each(source_doc.items || [], function(i, row) {
							if(row.qty > flt(item_qty_map[row.item_code])) {
								already_set = false;
								return false;
							}
						})
					})

					if(already_set) {
						frappe.msgprint(__("You have already selected items from {0} {1}",
							[opts.source_doctype, src]));
						return;
					}

				})
			}
		}

		return frappe.call({
			// Sometimes we hit the limit for URL length of a GET request
			// as we send the full target_doc. Hence this is a POST request.
			type: "POST",
			method: 'frappe.model.mapper.map_docs',
			args: {
				"method": opts.method,
				"source_names": opts.source_name,
				"target_doc": cur_frm.doc,
			},
			callback: function(r) {
				if(!r.exc) {
					var doc = frappe.model.sync(r.message);
					cur_frm.dirty();
					cur_frm.refresh();
				}
			}
		});
	}
	if(opts.source_doctype) {
		console.log(opts.setters)
		var d = new frappe.ui.form.MultiSelectDialog({
			doctype: opts.source_doctype,
			target: opts.target,
			date_field: opts.date_field || undefined,
			setters: opts.setters,
			get_query: opts.get_query,
			action: function(selections, args) {
				let values = selections;
				if(values.length === 0){
					frappe.msgprint(__("Please select {0}", [opts.source_doctype]))
					return;
				}
				if(values.length  > 1){
					frappe.msgprint(__("You cannot select more than pne {0}", [opts.source_doctype]))
					return;
				}
				opts.source_name = values;
				opts.setters = args;
				d.dialog.hide();
				_map();
			},
		});
		console.log("dialog: ")
		console.log(d);
	} else if(opts.source_name) {
		opts.source_name = [opts.source_name];
		_map();
	}
}

erpnext.stock.DeliveryNoteController = erpnext.selling.SellingController.extend({
	refresh: function(doc, dt, dn) {
		this._super();
		if (!doc.is_return && doc.status!="Closed") {
			if(flt(doc.per_installed, 2) < 100 && doc.docstatus==1)
				cur_frm.add_custom_button(__('Installation Note'), this.make_installation_note, __("Make"));

			if (doc.docstatus==1) {
				cur_frm.add_custom_button(__('Sales Return'), this.make_sales_return, __("Make"));
			}

			if(doc.docstatus==0 && !doc.__islocal) {
				cur_frm.add_custom_button(__('Packing Slip'),
					cur_frm.cscript['Make Packing Slip'], __("Make"));
			}

			if (!doc.__islocal && doc.docstatus==1) {
				cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
			}

			if (this.frm.doc.docstatus===0) {
				cur_frm.add_custom_button(__('Sales Order'),
					function() {
						erpnext.utils.map_current_doc({
							method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
							source_doctype: "Sales Order",
							get_query_filters: {
								docstatus: 1,
								status: ["!=", "Closed"],
								per_delivered: ["<", 99.99],
								project: cur_frm.doc.project || undefined,
								customer: cur_frm.doc.customer || undefined,
								company: cur_frm.doc.company
							}
						})
					}, __("Get items from"));
					// this.frm.add_custom_button(__('Sales Order Approval'),
					// function() {
					// 	map_current_doc_new({
					// 		method: "pmo.project_services.doctype.project_sales_order_approval.project_sales_order_approval.make_delivery_note",
					// 		source_doctype: "Project Sales Order Approval",
					// 		target: me.frm,
					// 		setters: {
					// 			customer: me.frm.doc.customer || undefined,
					// 		},
					// 		get_query_filters: {
					// 			docstatus: 0,
					// 			workflow_state: "Approved by PMO Director",
					// 			project_name: me.frm.doc.project || undefined,
					// 			date_delivered:  undefined
					// 		}
					// 	})
					// }, __("Get items from"));
			}
		}

		if (doc.docstatus==1) {
			this.show_stock_ledger();
			if (cint(frappe.defaults.get_default("auto_accounting_for_stock"))) {
				this.show_general_ledger();
			}
			if (this.frm.has_perm("submit") && doc.status !== "Closed") {
				cur_frm.add_custom_button(__("Close"), this.close_delivery_note, __("Status"))
			}
		}

		if(doc.docstatus==1 && !doc.is_return && doc.status!="Closed" && flt(doc.per_billed) < 100) {
			// show Make Invoice button only if Delivery Note is not created from Sales Invoice
			var from_sales_invoice = false;
			from_sales_invoice = cur_frm.doc.items.some(function(item) {
				return item.against_sales_invoice ? true : false;
			});

			if(!from_sales_invoice)
				cur_frm.add_custom_button(__('Invoice'), this.make_sales_invoice, __("Make"));
		}

		if(doc.docstatus==1 && doc.status === "Closed" && this.frm.has_perm("submit")) {
			cur_frm.add_custom_button(__('Reopen'), this.reopen_delivery_note, __("Status"))
		}
		erpnext.stock.delivery_note.set_print_hide(doc, dt, dn);

		// unhide expense_account and cost_center is auto_accounting_for_stock enabled
		var aii_enabled = cint(sys_defaults.auto_accounting_for_stock)
		// cur_frm.fields_dict["items"].grid.set_column_disp(["expense_account", "cost_center"], aii_enabled);
	},

	make_sales_invoice: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
			frm: cur_frm
		})
	},

	make_installation_note: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.delivery_note.delivery_note.make_installation_note",
			frm: cur_frm
		});
	},

	make_sales_return: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_return",
			frm: cur_frm
		})
	},

	tc_name: function() {
		this.get_terms();
	},

	items_on_form_rendered: function(doc, grid_row) {
		erpnext.setup_serial_no();
	},

	close_delivery_note: function(doc){
		cur_frm.cscript.update_status("Closed")
	},

	reopen_delivery_note : function() {
		cur_frm.cscript.update_status("Submitted")
	}

});





frappe.ui.form.on('Delivery Note Item', {
	 item_code: function(frm, cdt, cdn){
	 	var d = locals[cdt][cdn];
          frappe.call({
              method: "frappe.client.get_list",
             args: {
                  doctype: "Item",
                  fields: ["name", "default_warehouse"],
                 filters: { "name": d.item_code }
              },
              callback: function(r, rt) {
                 if (r.message) {
                     frappe.model.set_value(cdt, cdn, "warehouse", r.message[0].default_warehouse);
                 }
            }
         });
 },
	qty: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];

        for(var row= 0;row<cur_frm.doc.items.length;row++){

	        var qty = cur_frm.doc.items[row].qty
			if(qty){
				qty=qty
			}else{
				qty=0
			}

		}


   //      frappe.call({
   //          "method": "validate_bundle_qty_number",
   //          args: {
   //              'qty': qty,
   //          },
   //          doc: cur_frm.doc,
   //          callback: function(r){
			// 	if(r.message==1){
			// 		frappe.model.set_value(cdt, cdn, "qty", );
			// 	}
			// },
   //      });
        
    
    }
    

});




// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.stock.DeliveryNoteController({frm: cur_frm}));

cur_frm.cscript.new_contact = function(){
	tn = frappe.model.make_new_doc_and_get_name('Contact');
	locals['Contact'][tn].is_customer = 1;
	if(doc.customer) locals['Contact'][tn].customer = doc.customer;
	frappe.set_route('Form', 'Contact', tn);
}


cur_frm.cscript.update_status = function(status) {
	frappe.ui.form.is_saving = true;
	frappe.call({
		method:"erpnext.stock.doctype.delivery_note.delivery_note.update_delivery_note_status",
		args: {docname: cur_frm.doc.name, status: status},
		callback: function(r){
			if(!r.exc)
				cur_frm.reload_doc();
		},
		always: function(){
			frappe.ui.form.is_saving = false;
		}
	})
}

// ***************** Get project name *****************
// cur_frm.fields_dict['project'].get_query = function(doc, cdt, cdn) {
// 	return {
// 		query: "erpnext.controllers.queries.get_project_name",
// 		filters: {
// 			'customer': doc.customer
// 		}
// 	}
// }

cur_frm.fields_dict['transporter_name'].get_query = function(doc) {
	return{
		filters: { 'supplier_type': "transporter" }
	}
}

cur_frm.cscript['Make Packing Slip'] = function() {
	frappe.model.open_mapped_doc({
		method: "erpnext.stock.doctype.delivery_note.delivery_note.make_packing_slip",
		frm: cur_frm
	})
}

erpnext.stock.delivery_note.set_print_hide = function(doc, cdt, cdn){
	var dn_fields = frappe.meta.docfield_map['Delivery Note'];
	var dn_item_fields = frappe.meta.docfield_map['Delivery Note Item'];
	var dn_fields_copy = dn_fields;
	var dn_item_fields_copy = dn_item_fields;

	if (doc.print_without_amount) {
		dn_fields['currency'].print_hide = 1;
		dn_item_fields['rate'].print_hide = 1;
		dn_item_fields['discount_percentage'].print_hide = 1;
		dn_item_fields['price_list_rate'].print_hide = 1;
		dn_item_fields['amount'].print_hide = 1;
		dn_fields['taxes'].print_hide = 1;
	} else {
		if (dn_fields_copy['currency'].print_hide != 1)
			dn_fields['currency'].print_hide = 0;
		if (dn_item_fields_copy['rate'].print_hide != 1)
			dn_item_fields['rate'].print_hide = 0;
		if (dn_item_fields_copy['amount'].print_hide != 1)
			dn_item_fields['amount'].print_hide = 0;
		if (dn_fields_copy['taxes'].print_hide != 1)
			dn_fields['taxes'].print_hide = 0;
	}
}

cur_frm.cscript.print_without_amount = function(doc, cdt, cdn) {
	erpnext.stock.delivery_note.set_print_hide(doc, cdt, cdn);
}

cur_frm.cscript.on_submit = function(doc, cdt, cdn) {
	if(cint(frappe.boot.notification_settings.delivery_note)) {
		cur_frm.email_doc(frappe.boot.notification_settings.delivery_note_message);
	}
}

if (sys_defaults.auto_accounting_for_stock) {

	cur_frm.cscript.expense_account = function(doc, cdt, cdn){
		var d = locals[cdt][cdn];
		if(d.expense_account) {
			var cl = doc["items"] || [];
			for(var i = 0; i < cl.length; i++){
				if(!cl[i].expense_account) cl[i].expense_account = d.expense_account;
			}
		}
		refresh_field("items");
	}

	// expense account
	cur_frm.fields_dict['items'].grid.get_field('expense_account').get_query = function(doc) {
		return {
			filters: {
				"report_type": "Profit and Loss",
				"company": doc.company,
				"is_group": 0
			}
		}
	}

	// cost center
	cur_frm.cscript.cost_center = function(doc, cdt, cdn){
		var d = locals[cdt][cdn];
		if(d.cost_center) {
			var cl = doc["items"] || [];
			for(var i = 0; i < cl.length; i++){
				if(!cl[i].cost_center) cl[i].cost_center = d.cost_center;
			}
		}
		refresh_field("items");
	}

	cur_frm.fields_dict.items.grid.get_field("cost_center").get_query = function(doc) {
		return {

			filters: {
				'company': doc.company,
				"is_group": 0
			}
		}
	}
	

}
