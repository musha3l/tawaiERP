// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.buying");

{% include 'erpnext/buying/doctype/purchase_common/purchase_common.js' %};
frappe.ui.form.on("Purchase Order", {
    setup: function(frm) {
        frm.custom_make_buttons = {
            'Purchase Receipt': 'Receive',
            'Purchase Invoice': 'Invoice',
            'Stock Entry': 'Material to Supplier'
        }
    },
    refresh: function(frm){
        if (cur_frm.doc.workflow_state){
            if(cur_frm.doc.workflow_state == "Pending" || cur_frm.doc.workflow_state == "Reviewed By Purchase Manager"){
                frappe.call({
                    "method": "has_requester_perm",
                    "doc": cur_frm.doc,
                    "freeze": true,
                    callback: function(r) {
                    	console.log('**************')
                    	console.log(r.message)
                    	console.log('**************')
                    	
                        if(frappe.session.user != "Administrator"){
                            if (frappe.session.user != r.message){
                                cur_frm.page.clear_actions_menu();
                            }
                        }
                    }
                });
            }
        }
        if (cur_frm.doc.docstatus == 1 && frappe.user_roles.indexOf("Purchase Manager") != -1 && cur_frm.doc.contact_email){
        cur_frm.add_custom_button(__("Send Supplier Emails"), function() {
                frappe.call({
                    method: 'supplier_po_mail',
                    doc: cur_frm.doc,
                    freeze: true
                });
            });
        }  
    	// if (cur_frm.doc.workflow_state && cur_frm.doc.workflow_state == "Rejected By CEO(tc)"){
	    //     frappe.call({
	    //         "method": "frappe.client.get_value",
	    //         "order_by": "modified asc",
	    //         "args": {
	    //             "doctype": "Version",
	    //             "filters": {"docname":cur_frm.doc.name},
	    //             "fieldname": "data"
	    //         },
	    //         callback: function(res){
	    //             if (res && !res.exc){
	    //             	var data = JSON.parse(res.message.data);
	    //             	// console.log(JSON.parse(res.message.data));
	    //             	if ("changed" in data){
	    //             		var fields = ["tc_name", "terms", "payment_plan", "shipment_terms", "definitions"];
		   //              	for(var i in data.changed){
		   //              		console.log(data.changed[i][0]);
		   //              		if (fields.indexOf(data.changed[i][0]) != -1){
		   //              			cur_frm.set_value(data.changed[i][0], data.changed[i][1]);
		   //              		}
		   //              	}
	    //             	}
	    //                 // console.log(JSON.parse(res.message));
	    //             }
	    //         }
	    //     });
	    // }

        // if (!cur_frm.doc.__islocal) {
        //     for (var key in cur_frm.fields_dict) {
        //         cur_frm.fields_dict[key].df.read_only = 1;
        //     }
        //     cur_frm.fields_dict["msg_to_supplier"].df.read_only = 0;
        //     cur_frm.fields_dict["msg_section"].df.read_only = 0;
        //     cur_frm.disable_save();
        // } else {
        //     cur_frm.enable_save();
        // }
    },
    onload: function(frm) {
        // frm.refresh();
        erpnext.queries.setup_queries(frm, "Warehouse", function() {
            return erpnext.queries.warehouse(frm.doc);
        });

        frm.set_indicator_formatter('item_code',
            function(doc) { return (doc.qty <= doc.received_qty) ? "green" : "orange" })

    },
    onload_post_render: function(frm){
        frm.add_fetch("quotation_opening", "reason", "reason");   
    },
    after_save: function(frm, cdt, cdn){
        if (frm.doc.workflow_state && frm.doc.workflow_state.indexOf("Rejected") != -1){

            frappe.prompt([
                {
                    fieldtype: 'Small Text',
                    reqd: true,
                    fieldname: 'reason'
                }],
                function(args){
                    validated = true;
                    frappe.call({
                        method: 'frappe.core.doctype.communication.email.make',
                        args: {
                            doctype: frm.doctype,
                            name: frm.docname,
                            subject: format(__('Reason for {0}'), [frm.doc.workflow_state]),
                            content: args.reason,
                            send_mail: false,
                            send_me_a_copy: false,
                            communication_medium: 'Other',
                            sent_or_received: 'Sent'
                        },
                        callback: function(res){
                            if (res && !res.exc){
                                frappe.call({
                                    method: 'frappe.client.set_value',
                                    args: {
                                        doctype: frm.doctype,
                                        name: frm.docname,
                                        fieldname: 'rejection_reason',
                                        value: args.reason
                                    },
                                    callback: function(res){
                                        if (res && !res.exc){
                                         	// if (cur_frm.doc.workflow_state == "Rejected By CEO(tc)"){
									        // 	cur_frm.set_value("tc_name", cur_frm.doc.old_tc_name);
									        // 	cur_frm.set_value("terms", cur_frm.doc.old_terms);
									        // 	cur_frm.set_value("payment_plan", cur_frm.doc.old_payment_plan);
									        // 	cur_frm.set_value("shipment_terms", cur_frm.doc.old_shipment_terms);
									        // 	cur_frm.set_value("definitions", cur_frm.doc.old_definitions);
								        	// }
                                            frm.reload_doc();
                                        }
                                    }
                                });
                            }
                        }
                    });
                },
                __('Reason for ') + __(frm.doc.workflow_state),
                __('End as Rejected')
            )
        }
    }



});

erpnext.buying.PurchaseOrderController = erpnext.buying.BuyingController.extend({
    refresh: function(doc) {
        var me = this;
        this._super();
        var allow_receipt = false;
        var is_drop_ship = false;

        for (var i in cur_frm.doc.items) {
            var item = cur_frm.doc.items[i];
            if (item.delivered_by_supplier !== 1) {
                allow_receipt = true;
            } else {
                is_drop_ship = true;
            }

            if (is_drop_ship && allow_receipt) {
                break;
            }
        }

        cur_frm.set_df_property("drop_ship", "hidden", !is_drop_ship);

        if (doc.docstatus == 1 && !in_list(["Closed", "Delivered"], doc.status)) {
            if (this.frm.has_perm("submit")) {
                if (flt(doc.per_billed, 2) < 100 || doc.per_received < 100) {
                    //Added as this allowed for accounts manager role
                    if(frappe.user_roles.indexOf("Accounts Manager") != -1){
                        cur_frm.add_custom_button(__('Close'), this.close_purchase_order, __("Status"));
                    }
                }
            }

            if (is_drop_ship && doc.status != "Delivered") {
                cur_frm.add_custom_button(__('Delivered'),
                    this.delivered_by_supplier, __("Status"));

                cur_frm.page.set_inner_btn_group_as_primary(__("Status"));
            }
        } else if (doc.docstatus === 0) {
            // cur_frm.cscript.add_from_mappers();
        }

        if (doc.docstatus == 1 && in_list(["Closed", "Delivered"], doc.status)) {
            if (this.frm.has_perm("submit")) {
                //Added as this allowed for accounts manager role
                if(frappe.user_roles.indexOf("Accounts Manager") != -1){
                    cur_frm.add_custom_button(__('Re-open'), this.unclose_purchase_order, __("Status"));
                }
            }
        }

        if (doc.docstatus == 1 && doc.status != "Closed") {
            frappe.call({
                "method": "has_requester_perm",
                "doc": cur_frm.doc,
                "freeze": true,
                callback: function(r) {
                    if(frappe.session.user == "Administrator" || frappe.session.user == r.message || frappe.user_roles.indexOf("Accounts Manager") != -1){
                        if (flt(doc.per_received, 2) < 100 && allow_receipt) {
                            cur_frm.add_custom_button(__('Receive'), me.make_purchase_receipt, __("Make"));

                            if (doc.is_subcontracted === "Yes") {
                                cur_frm.add_custom_button(__('Material to Supplier'),
                                    function() { me.make_stock_entry(); }, __("Transfer"));
                            }
                        }
                    }
                }
            });
            // if (flt(doc.per_received, 2) < 100 && allow_receipt) {
            //     cur_frm.add_custom_button(__('Receive'), this.make_purchase_receipt, __("Make"));

            //     if (doc.is_subcontracted === "Yes") {
            //         cur_frm.add_custom_button(__('Material to Supplier'),
            //             function() { me.make_stock_entry(); }, __("Transfer"));
            //     }
            // }
            // && flt(doc.per_received, 2) === 100 added by ahmed madi 
            if (flt(doc.per_billed, 2) < 100 && flt(doc.per_received, 2) === 100)
                cur_frm.add_custom_button(__('Invoice'),
                    this.make_purchase_invoice, __("Make"));

            if (flt(doc.per_billed) == 0 && doc.status != "Delivered") {
                cur_frm.add_custom_button(__('Payment'), cur_frm.cscript.make_payment_entry, __("Make"));
            }
            cur_frm.page.set_inner_btn_group_as_primary(__("Make"));

        }

  
    },

    get_items_from_open_material_requests: function() {
        erpnext.utils.map_current_doc({
            method: "erpnext.stock.doctype.material_request.material_request.make_purchase_order_based_on_supplier",
            source_name: this.frm.doc.supplier,
            get_query_filters: {
                docstatus: ["!=", 2],
            }
        });
    },

    validate: function() {
        // set default schedule date as today if missing.
        (this.frm.doc.items || []).forEach(function(d) {
            if (!d.schedule_date) {
                d.schedule_date = frappe.datetime.nowdate();
            }
        });
    },
    make_stock_entry: function() {
        var items = $.map(cur_frm.doc.items, function(d) { return d.bom ? d.item_code : false; });
        var me = this;

        if (items.length === 1) {
            me._make_stock_entry(items[0]);
            return;
        }
        frappe.prompt({
            fieldname: "item",
            options: items,
            fieldtype: "Select",
            label: __("Select Item for Transfer"),
            reqd: 1
        }, function(data) {
            me._make_stock_entry(data.item);
        }, __("Select Item"), __("Make"));
    },

    _make_stock_entry: function(item) {
        frappe.call({
            method: "erpnext.buying.doctype.purchase_order.purchase_order.make_stock_entry",
            args: {
                purchase_order: cur_frm.doc.name,
                item_code: item
            },
            callback: function(r) {
                var doclist = frappe.model.sync(r.message);
                frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
            }
        });
    },

    make_purchase_receipt: function() {
        frappe.model.open_mapped_doc({
            method: "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_receipt",
            frm: cur_frm
        })
    },

    make_purchase_invoice: function() {
        frappe.model.open_mapped_doc({
            method: "erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice",
            frm: cur_frm
        })
    },

    add_from_mappers: function() {
        cur_frm.add_custom_button(__('Material Request'),
            function() {
                erpnext.utils.map_current_doc({
                    method: "erpnext.stock.doctype.material_request.material_request.make_purchase_order",
                    source_doctype: "Material Request",
                    get_query_filters: {
                        material_request_type: "Purchase",
                        docstatus: 1,
                        status: ["!=", "Stopped"],
                        per_ordered: ["<", 99.99],
                        company: cur_frm.doc.company
                    }
                })
            }, __("Add items from"));

        cur_frm.add_custom_button(__('Supplier Quotation'),
            function() {
                erpnext.utils.map_current_doc({
                    method: "erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_purchase_order",
                    source_doctype: "Supplier Quotation",
                    get_query_filters: {
                        docstatus: 1,
                        status: ["!=", "Stopped"],
                        company: cur_frm.doc.company
                    }
                })
            }, __("Add items from"));

    },

    tc_name: function() {
        this.get_terms();
    },

    items_add: function(doc, cdt, cdn) {
        var row = frappe.get_doc(cdt, cdn);
        this.frm.script_manager.copy_from_first_row("items", row, ["schedule_date"]);
    },

    unclose_purchase_order: function() {
        cur_frm.cscript.update_status('Re-open', 'Submitted')
    },

    close_purchase_order: function() {
        cur_frm.cscript.update_status('Close', 'Closed')
    },

    delivered_by_supplier: function() {
        cur_frm.cscript.update_status('Deliver', 'Delivered')
    },

    get_last_purchase_rate: function() {
        frappe.call({
            "method": "get_last_purchase_rate",
            "doc": cur_frm.doc,
            callback: function(r, rt) {
                cur_frm.dirty();
                cur_frm.cscript.calculate_taxes_and_totals();
            }
        })
    }

});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.buying.PurchaseOrderController({ frm: cur_frm }));

cur_frm.cscript.update_status = function(label, status) {
    frappe.call({
        method: "erpnext.buying.doctype.purchase_order.purchase_order.update_status",
        args: { status: status, name: cur_frm.doc.name },
        callback: function(r) {
            cur_frm.set_value("status", status);
            cur_frm.reload_doc();
        }
    })
}

cur_frm.fields_dict['supplier_address'].get_query = function(doc, cdt, cdn) {
    return {
        filters: { 'supplier': doc.supplier }
    }
}

cur_frm.fields_dict['contact_person'].get_query = function(doc, cdt, cdn) {
    return {
        filters: { 'supplier': doc.supplier }
    }
}

cur_frm.fields_dict['items'].grid.get_field('project').get_query = function(doc, cdt, cdn) {
    return {
        filters: [
            ['Project', 'status', 'not in', 'Completed, Cancelled']
        ]
    }
}

cur_frm.fields_dict['items'].grid.get_field('bom').get_query = function(doc, cdt, cdn) {
    var d = locals[cdt][cdn]
    return {
        filters: [
            ['BOM', 'item', '=', d.item_code],
            ['BOM', 'is_active', '=', '1'],
            ['BOM', 'docstatus', '=', '1']
        ]
    }
}

// cur_frm.cscript.on_submit = function(doc, cdt, cdn) {
//     if (cint(frappe.boot.notification_settings.purchase_order)) {
//         cur_frm.email_doc(frappe.boot.notification_settings.purchase_order_message);
//     }
// }

cur_frm.cscript.schedule_date = function(doc, cdt, cdn) {
    erpnext.utils.copy_value_in_all_row(doc, cdt, cdn, "items", "schedule_date");
}

frappe.provide("erpnext.buying");

frappe.ui.form.on("Purchase Order", "is_subcontracted", function(frm) {
    if (frm.doc.is_subcontracted === "Yes") {
        erpnext.buying.get_default_bom(frm);
    }
});
cur_frm.cscript.custom_item_code = function(doc, cdt, cdn){
    var d = locals[cdt][cdn];
    if (cur_frm.doc.project){
        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Project",
                fields: ["name", "default_warehouse"],
                filters: { "name": cur_frm.doc.project }
            },
            callback: function(r, rt) {
                // console.log(r.message);
                if (r.message) {
                    frappe.model.set_value(d.doctype, d.name, "project", r.message[0].name);
                    frappe.model.set_value(d.doctype, d.name, "warehouse", r.message[0].default_warehouse);
                }
            }
        });
    }
}
// cur_frm.cscript.custom_on_update_after_submit = function(){
// 	alert("ddffd");
// }