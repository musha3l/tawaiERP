// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// print heading
cur_frm.pformat.print_heading = 'Invoice';
cur_frm.add_fetch('project', 'payment_terms', 'payment_terms');
cur_frm.add_fetch('payment_terms', 'debit_to', 'debit_to');

{% include 'erpnext/selling/sales_common.js' %};

frappe.provide("erpnext.accounts");
erpnext.accounts.SalesInvoiceController = erpnext.selling.SellingController.extend({
	onload: function() {
		var me = this;
		this._super();

		if(!this.frm.doc.__islocal && !this.frm.doc.customer && this.frm.doc.debit_to) {
			// show debit_to in print format
			this.frm.set_df_property("debit_to", "print_hide", 0);
		}

		erpnext.queries.setup_queries(this.frm, "Warehouse", function() {
			return erpnext.queries.warehouse(me.frm.doc);
		});

		if(this.frm.doc.__islocal && this.frm.doc.is_pos) {
			//Load pos profile data on the invoice if the default value of Is POS is 1

			me.frm.script_manager.trigger("is_pos");
			me.frm.refresh_fields();
		}
	},

	refresh: function(doc, dt, dn) {
		this._super();
		if(cur_frm.msgbox && cur_frm.msgbox.$wrapper.is(":visible")) {
			// hide new msgbox
			cur_frm.msgbox.hide();
		}

		this.frm.toggle_reqd("due_date", !this.frm.doc.is_return);

		this.show_general_ledger();

		if(doc.update_stock) this.show_stock_ledger();

		if(doc.docstatus==1 && !doc.is_return) {

			var is_delivered_by_supplier = false;

			is_delivered_by_supplier = cur_frm.doc.items.some(function(item){
				return item.is_delivered_by_supplier ? true : false;
			})

			if(doc.outstanding_amount >= 0 || Math.abs(flt(doc.outstanding_amount)) < flt(doc.grand_total)) {
				cur_frm.add_custom_button(doc.update_stock ? __('Sales Return') : __('Credit Note'),
					this.make_sales_return, __("Make"));
				cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
			}

			if(cint(doc.update_stock)!=1) {
				// show Make Delivery Note button only if Sales Invoice is not created from Delivery Note
				var from_delivery_note = false;
				from_delivery_note = cur_frm.doc.items
					.some(function(item) {
						return item.delivery_note ? true : false;
					});

				if(!from_delivery_note && !is_delivered_by_supplier) {
					cur_frm.add_custom_button(__('Delivery'), cur_frm.cscript['Make Delivery Note'],
						__("Make"));
				}
			}

			if(doc.outstanding_amount!=0 && !cint(doc.is_return)) {
				cur_frm.add_custom_button(__('Payment'), this.make_payment_entry, __("Make"));
			}

			if(doc.outstanding_amount>0 && !cint(doc.is_return)) {
				cur_frm.add_custom_button(__('Payment Request'), this.make_payment_request, __("Make"));
			}


		}

		// Show buttons only when pos view is active
		if (cint(doc.docstatus==0) && cur_frm.page.current_view_name!=="pos" && !doc.is_return) {
			cur_frm.cscript.sales_order_btn();
			cur_frm.cscript.delivery_note_btn();
		}

		if(in_list(frappe.user_roles, "Accounts Manager")) {
			console.log("HIT");
			cur_frm.set_df_property('posting_date', 'read_only', 0);
			cur_frm.set_df_property('due_date', 'read_only', 0);
			cur_frm.set_df_property('delivery_date', 'read_only', 0);
			cur_frm.refresh_field("posting_date")
			console.log("HIT2");

		}

		this.set_default_print_format();
	},

	set_default_print_format: function() {
		// set default print format to POS type
		if(cur_frm.doc.is_pos) {
			if(cur_frm.pos_print_format) {
				cur_frm.meta._default_print_format = cur_frm.meta.default_print_format;
				cur_frm.meta.default_print_format = cur_frm.pos_print_format;
			}
		} else {
			if(cur_frm.meta._default_print_format) {
				cur_frm.meta.default_print_format = cur_frm.meta._default_print_format;
				cur_frm.meta._default_print_format = null;
			}
		}
	},

	sales_order_btn: function() {
		this.$sales_order_btn = cur_frm.add_custom_button(__('Sales Order'),
			function() {
				erpnext.utils.map_current_doc({
					method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
					source_doctype: "Sales Order",
					get_query_filters: {
						docstatus: 1,
						status: ["!=", "Closed"],
						per_billed: ["<", 99.99],
						customer: cur_frm.doc.customer || undefined,
						company: cur_frm.doc.company
					}
				})
			}, __("Get items from"));
	},

	delivery_note_btn: function() {
		this.$delivery_note_btn = cur_frm.add_custom_button(__('Delivery Note'),
			function() {
				erpnext.utils.map_current_doc({
					method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
					source_doctype: "Delivery Note",
					get_query: function() {
						var filters = {
							company: cur_frm.doc.company
						};
						if(cur_frm.doc.customer) filters["customer"] = cur_frm.doc.customer;
						return {
							query: "erpnext.controllers.queries.get_delivery_notes_to_be_billed",
							filters: filters
						};
					}
				});
			}, __("Get items from"));
	},

	tc_name: function() {
		this.get_terms();
	},

	customer: function() {
		var me = this;
		if(this.frm.updating_party_details) return;

		erpnext.utils.get_party_details(this.frm,
			"erpnext.accounts.party.get_party_details", {
				posting_date: this.frm.doc.posting_date,
				party: this.frm.doc.customer,
				party_type: "Customer",
				account: this.frm.doc.debit_to,
				price_list: this.frm.doc.selling_price_list,
			}, function() {
			me.apply_pricing_rule();
		})
	},

	debit_to: function() {
		var me = this;
		if(this.frm.doc.debit_to) {
			me.frm.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Account",
					fieldname: "account_currency",
					filters: { name: me.frm.doc.debit_to },
				},
				callback: function(r, rt) {
					if(r.message) {
						me.frm.set_value("party_account_currency", r.message.account_currency);
						me.set_dynamic_labels();
					}
				}
			});
		}
	},

	allocated_amount: function() {
		this.calculate_total_advance();
		this.frm.refresh_fields();
	},

	write_off_outstanding_amount_automatically: function() {
		if(cint(this.frm.doc.write_off_outstanding_amount_automatically)) {
			frappe.model.round_floats_in(this.frm.doc, ["grand_total", "paid_amount"]);
			// this will make outstanding amount 0
			this.frm.set_value("write_off_amount",
				flt(this.frm.doc.grand_total - this.frm.doc.paid_amount - this.frm.doc.total_advance, precision("write_off_amount"))
			);
			this.frm.toggle_enable("write_off_amount", false);

		} else {
			this.frm.toggle_enable("write_off_amount", true);
		}

		this.calculate_outstanding_amount(false);
		this.frm.refresh_fields();
	},

	write_off_amount: function() {
		this.set_in_company_currency(this.frm.doc, ["write_off_amount"]);
		this.write_off_outstanding_amount_automatically();
	},

	items_add: function(doc, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn);
		this.frm.script_manager.copy_from_first_row("items", row, ["income_account", "cost_center"]);
	},

	set_dynamic_labels: function() {
		this._super();
		this.hide_fields(this.frm.doc);
	},

	items_on_form_rendered: function() {
		erpnext.setup_serial_no();
	},

	make_sales_return: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_sales_return",
			frm: cur_frm
		})
	},

	asset: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if(row.asset) {
			frappe.call({
				method: erpnext.accounts.doctype.asset.depreciation.get_disposal_account_and_cost_center,
				args: {
					"company": frm.doc.company
				},
				callback: function(r, rt) {
					frappe.model.set_value(cdt, cdn, "income_account", r.message[0]);
					frappe.model.set_value(cdt, cdn, "cost_center", r.message[1]);
				}
			})
		}
	},

	is_pos: function(frm){
		if(this.frm.doc.is_pos) {
			if(!this.frm.doc.company) {
				this.frm.set_value("is_pos", 0);
				msgprint(__("Please specify Company to proceed"));
			} else {
				var me = this;
				return this.frm.call({
					doc: me.frm.doc,
					method: "set_missing_values",
					callback: function(r) {
						if(!r.exc) {
							if(r.message && r.message.print_format) {
								frm.pos_print_format = r.message.print_format;
							}
							me.frm.script_manager.trigger("update_stock");
							frappe.model.set_default_values(me.frm.doc);
							me.set_dynamic_labels();
							me.calculate_taxes_and_totals();
						}
					}
				});
			}
		}
		else this.frm.trigger("refresh")
	},

	amount: function(){
		this.write_off_outstanding_amount_automatically()
	},

	change_amount: function(){
		if(this.frm.doc.paid_amount > this.frm.doc.grand_total){
			this.calculate_write_off_amount()
		}else {
			this.frm.set_value("change_amount", 0.0)
		}

		this.frm.refresh_fields();
	}

});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.accounts.SalesInvoiceController({frm: cur_frm}));

// Hide Fields
// ------------
cur_frm.cscript.custom_total_from_project_cost = function(doc) {
		frappe.call({
				method: "set_items_by_project",
				doc:doc,
				callback: function(r) {
				console.log(r.message)
				cur_frm.refresh_field('items');
				}
			});
}
cur_frm.cscript.custom_payment_term_unit = function(doc) {
	frappe.call({
				method: "get_payment_units_share",
				doc:doc,
				callback: function(r) {
				console.log(r.message)
				cur_frm.set_value("share_payment_terms",r.message)
				}
			});
	frappe.call({
				method: "set_items_by_project",
				doc:doc,
				callback: function(r) {
				console.log(r.message)
				cur_frm.refresh_field('items');
				}
			});
}
cur_frm.cscript.custom_payment_terms = function(doc) {
	frappe.call({
				method: "get_payment_units",
				doc:doc,
				callback: function(r) {
				console.log(r.message)
				 var options = [];
				 (r.message || []).forEach(function(row){   // start a loop over all options in the response, or in a empty list;
					 console.log( row.key,row.value)
					 console.log( "row",row)
				   options.push({'value': row["name"], 'label': row["Term"]}) // makes a option entry 'value' and 'label'
				 });
				cur_frm.set_df_property('payment_term_unit', 'options', options);
				cur_frm.refresh_field('payment_term_unit');
				}
			});
}
cur_frm.cscript.hide_fields = function(doc) {
	parent_fields = ['project', 'due_date', 'is_opening', 'source', 'total_advance', 'get_advances',
		'advances', 'sales_partner', 'commission_rate', 'total_commission', 'advances', 'from_date', 'to_date'];

	if(cint(doc.is_pos) == 1) {
		hide_field(parent_fields);
	} else {
		for (i in parent_fields) {
			var docfield = frappe.meta.docfield_map[doc.doctype][parent_fields[i]];
			if(!docfield.hidden) unhide_field(parent_fields[i]);
		}
	}

	item_fields_stock = ['serial_no', 'batch_no', 'actual_qty', 'expense_account', 'warehouse', 'expense_account', 'warehouse']
	cur_frm.fields_dict['items'].grid.set_column_disp(item_fields_stock,
		(cint(doc.update_stock)==1 || cint(doc.is_return)==1 ? true : false));

	// India related fields
	if (frappe.boot.sysdefaults.country == 'India') unhide_field(['c_form_applicable', 'c_form_no']);
	else hide_field(['c_form_applicable', 'c_form_no']);

	this.frm.toggle_enable("write_off_amount", !!!cint(doc.write_off_outstanding_amount_automatically));

	cur_frm.refresh_fields();
}

cur_frm.cscript.update_stock = function(doc, dt, dn) {
	cur_frm.cscript.hide_fields(doc, dt, dn);
}

cur_frm.cscript['Make Delivery Note'] = function() {
	frappe.model.open_mapped_doc({
		method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.make_delivery_note",
		frm: cur_frm
	})
}

cur_frm.fields_dict.cash_bank_account.get_query = function(doc) {
	return {
		filters: [
			["Account", "account_type", "in", ["Cash", "Bank"]],
			["Account", "root_type", "=", "Asset"],
			["Account", "is_group", "=",0],
			["Account", "company", "=", doc.company]
		]
	}
}

cur_frm.fields_dict.write_off_account.get_query = function(doc) {
	return{
		filters:{
			'report_type': 'Profit and Loss',
			'is_group': 0,
			'company': doc.company
		}
	}
}

// Write off cost center
//-----------------------
cur_frm.fields_dict.write_off_cost_center.get_query = function(doc) {
	return{
		filters:{
			'is_group': 0,
			'company': doc.company
		}
	}
}

//project name
//--------------------------
cur_frm.fields_dict['project'].get_query = function(doc, cdt, cdn) {
	return{
		query: "erpnext.controllers.queries.get_project_name",
		filters: {'customer': doc.customer}
	}
}

// Income Account in Details Table
// --------------------------------
cur_frm.set_query("income_account", "items", function(doc) {
	return{
		query: "erpnext.controllers.queries.get_income_account",
		filters: {'company': doc.company}
	}
});

// expense account
if (sys_defaults.auto_accounting_for_stock) {
	cur_frm.fields_dict['items'].grid.get_field('expense_account').get_query = function(doc) {
		return {
			filters: {
				'report_type': 'Profit and Loss',
				'company': doc.company,
				"is_group": 0
			}
		}
	}
}


// Cost Center in Details Table
// -----------------------------
cur_frm.fields_dict["items"].grid.get_field("cost_center").get_query = function(doc) {
	return {
		filters: {
			'company': doc.company,
			"is_group": 0
		}
	}
}

cur_frm.cscript.income_account = function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	erpnext.utils.copy_value_in_all_row(doc, cdt, cdn, "items", "income_account");
	check_account_type_for_mandatory(d);
}

cur_frm.cscript.item_code = function(doc, cdt, cdn) {
	console.log("tesssst");
	// var d = locals[cdt][cdn];
	erpnext.utils.copy_value_in_all_row(doc, cdt, cdn, "items", "income_account");
	cur_frm.fields_dict.items.grid.toggle_reqd("cost_center", false);
}

cur_frm.cscript.expense_account = function(doc, cdt, cdn) {
	erpnext.utils.copy_value_in_all_row(doc, cdt, cdn, "items", "expense_account");
}

cur_frm.cscript.cost_center = function(doc, cdt, cdn) {
	erpnext.utils.copy_value_in_all_row(doc, cdt, cdn, "items", "cost_center");
}

cur_frm.cscript.on_submit = function(doc, cdt, cdn) {
	$.each(doc["items"], function(i, row) {
		if(row.delivery_note) frappe.model.clear_doc("Delivery Note", row.delivery_note)
	})

	if(cur_frm.doc.is_pos) {
		cur_frm.msgbox = frappe.msgprint(format('<a class="btn btn-primary" \
			onclick="cur_frm.print_preview.printit(true)" style="margin-right: 5px;">{0}</a>\
			<a class="btn btn-default" href="javascript:frappe.new_doc(cur_frm.doctype);">{1}</a>', [
			__('Print'), __('New')
		]));

	} else if(cint(frappe.boot.notification_settings.sales_invoice)) {
		cur_frm.email_doc(frappe.boot.notification_settings.sales_invoice_message);
	}
}

function check_account_type_for_mandatory(d){
    frappe.call({
        "method": "frappe.client.get_value",
        "args": {
            "doctype": "Account",
            "filters":{"name": d.income_account},
            "fieldname": "account_type"
        },
        callback: function(r){
            console.log("cost center",r.message);
						cur_frm.fields_dict.items.grid.toggle_reqd("cost_center", false);
            if (!r.exc) {
                if (r.message){
                    // cur_frm.fields_dict.items.grid.toggle_reqd("cost_center", r.message.account_type == "Income Account");
                }
                else{
                    // cur_frm.fields_dict.items.grid.toggle_reqd("cost_center", false);
                }
            }
        }
    });
}

cur_frm.set_query("debit_to", function(doc) {
	// filter on Account
	if (doc.customer) {
		return {
			filters: {
				'account_type': 'Receivable',
				'is_group': 0,
				'company': doc.company
			}
		}
	} else {
		return {
			filters: {
				'report_type': 'Balance Sheet',
				'is_group': 0,
				'company': doc.company
			}
		}
	}
});

cur_frm.set_query("asset", "items", function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	return {
		filters: [
			["Asset", "item_code", "=", d.item_code],
			["Asset", "docstatus", "=", 1],
			["Asset", "status", "in", ["Submitted", "Partially Depreciated", "Fully Depreciated"]],
			["Asset", "company", "=", doc.company]
		]
	}
});

frappe.ui.form.on('Sales Invoice', {
	setup: function(frm){
		frm.custom_make_buttons = {
			'Delivery Note': 'Delivery',
			'Sales Invoice': 'Sales Return',
			'Payment Request': 'Payment Request',
			'Payment': 'Payment Entry'
		},
		frm.fields_dict["timesheets"].grid.get_field("time_sheet").get_query = function(doc, cdt, cdn){
			return{
				query: "erpnext.projects.doctype.timesheet.timesheet.get_timesheet",
				filters: {'project': doc.project}
			}
		}
	},

	project: function(frm){
		frm.call({
			method: "add_timesheet_data",
			doc: frm.doc,
			callback: function(r, rt) {
				refresh_field(['timesheets'])
			}
		})
	},
	validate: function(frm){
		var total_billing = 0;
        $.each(frm.doc.project_payment_schedule_invoice || [], function (i, d) {
            total_billing += flt(d.billing_value);
        });

        var total_tax = 0;
        $.each(frm.doc.project_payment_schedule_invoice || [], function (i, d) {
            total_tax += flt(d.vat_value);
        });

        frm.set_value('total_control_billing', total_billing);
        frm.set_value('total_control_tax', total_tax);
        frm.set_value('total_after_advance', cur_frm.doc.total - total_billing);
        frm.set_value('total_vat_advance', Math.round(cur_frm.doc.total_taxes_and_charges - total_tax));
        frm.set_value('final_total', cur_frm.doc.total_after_advance + Math.round(cur_frm.doc.total_vat_advance));

	}
})

frappe.ui.form.on('Sales Invoice Timesheet', {
	time_sheet: function(frm, cdt, cdn){
		var d = locals[cdt][cdn];
		if(d.time_sheet) {
			frappe.call({
				method: "erpnext.projects.doctype.timesheet.timesheet.get_timesheet_data",
				args: {
					'name': d.time_sheet,
					'project': frm.doc.project || null
				},
				callback: function(r, rt) {
					if(r.message){
						data = r.message;
						frappe.model.set_value(cdt, cdn, "billing_hours", data.billing_hours);
						frappe.model.set_value(cdt, cdn, "billing_amount", data.billing_amount);
						frappe.model.set_value(cdt, cdn, "timesheet_detail", data.timesheet_detail);
						calculate_total_billing_amount(frm)
					}
				}
			})
		}
	}
})

var calculate_total_billing_amount =  function(frm) {
	var doc = frm.doc;

	doc.total_billing_amount = 0.0
	if(doc.timesheets) {
		$.each(doc.timesheets, function(index, data){
			doc.total_billing_amount += data.billing_amount
		})
	}

	refresh_field('total_billing_amount')
}
