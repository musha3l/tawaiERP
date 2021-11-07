// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
{% include "erpnext/public/js/controllers/accounts.js" %}

frappe.ui.form.on('Payment Entry', {
	onload: function(frm) {
		if(frm.doc.__islocal) {
			if (!frm.doc.paid_from) frm.set_value("paid_from_account_currency", null);
			if (!frm.doc.paid_to) frm.set_value("paid_to_account_currency", null);
		}
	},

	setup: function(frm) {
		var party_account_type = frm.doc.party_type=="Customer" ? "Receivable" : "Payable";

		frm.set_query("paid_from", function() {
			var party_account_type = in_list(["Customer", "Employee"], frm.doc.party_type) ?
				"Receivable" : "Payable";
			var account_types = in_list(["Pay", "Internal Transfer"], frm.doc.payment_type) ?
				["Bank", "Cash"] : party_account_type;
			
			if (frm.doc.payment_type == "Internal Transfer")
			{
				account_types = [
					"Accumulated Depreciation",
					"Bank",
					"Cash",
					"Chargeable",
					"Cost of Goods Sold",
					"Depreciation",
					"Equity",
					"Expense Account",
					"Expenses Included In Valuation",
					"Fixed Asset",
					"Income Account",
					"Payable",
					"Receivable",
					"Round Off",
					"Stock",
					"Stock Adjustment",
					"Stock Received But Not Billed",
					"Tax",
					"Temporary",
				]
			}
			return {
				filters: {
					"account_type": ["in", account_types],
					"is_group": 0,
					"company": frm.doc.company
				}
			}
		});

		frm.set_query("paid_to", function() {
			var party_account_type = in_list(["Customer", "Employee"], frm.doc.party_type) ?
				"Receivable" : "Payable";
			var account_types = in_list(["Receive", "Internal Transfer"], frm.doc.payment_type) ?
				["Bank", "Cash"] : party_account_type;
			if (frm.doc.payment_type == "Internal Transfer")
			{
				account_types = [
					"Accumulated Depreciation",
					"Bank",
					"Cash",
					"Chargeable",
					"Cost of Goods Sold",
					"Depreciation",
					"Equity",
					"Expense Account",
					"Expenses Included In Valuation",
					"Fixed Asset",
					"Income Account",
					"Payable",
					"Receivable",
					"Round Off",
					"Stock",
					"Stock Adjustment",
					"Stock Received But Not Billed",
					"Tax",
					"Temporary",
				]
			}
			return {
				filters: {
					"account_type": ["in", account_types],
					"is_group": 0,
					"company": frm.doc.company
				}
			}
		});

		frm.set_query("account", "deductions", function() {
			return {
				filters: {
					"is_group": 0,
					"company": frm.doc.company
				}
			}
		});

		frm.set_query("cost_center", "deductions", function() {
			return {
				filters: {
					"is_group": 0,
					"company": frm.doc.company
				}
			}
		});

		frm.set_query("reference_doctype", "references", function() {
			if (frm.doc.party_type=="Customer") {
				var doctypes = ["Sales Order", "Sales Invoice", "Journal Entry"];
			} else if (frm.doc.party_type=="Supplier") {
				var doctypes = ["Purchase Order", "Purchase Invoice", "Journal Entry"];
			} else {
				var doctypes = ["Journal Entry"];
			}

			return {
				filters: { "name": ["in", doctypes] }
			};
		});
	},

	refresh: function(frm) {
		erpnext.hide_company();
		frm.events.hide_unhide_fields(frm);
		frm.events.set_dynamic_labels(frm);
		frm.events.show_general_ledger(frm);

		if(frm.doc.docstatus === 1 && (frm.doc.payment_type === 'Receive' || frm.doc.payment_type === 'Pay')) {
			frm.events.add_journal_entry_button(frm, 'Return');
		}
	},

	/*
	* Return/Deposit in Make button after deciding which is appropriate.
	* @param {Frm} frm
	* @param {string} reversal_button - Label of button for reversal entry
	* @param {string} redeposit_button - Label of button for redeposit entry
	*/
	add_journal_entry_button: function(frm, reversal_button) {
		frm.events.add_button(frm, reversal_button, frm.events.show_return_journal_dialog);
	},

	/**
	* Wrapper over `add_custom_button`
	* @param {Frm} frm
	* @param {string} button_name
	* @param {function} fn
	* @param {string} primary_button_name
	*/
	add_button: function(frm, button_name, fn, primary_button_name='Make') {
		frm.add_custom_button(
			__(button_name),
			function() {
				fn(frm);
			},
			__(primary_button_name)
		);
	},

	get_journal_dialog: function(frm) {
		return new frappe.ui.Dialog({
			fields: [
				{
					fieldtype:'Date', reqd:1, label:'Posting Date',
					fieldname: 'posting_date'
				},
				{
					fieldtype:'Link', label:'Cost Center',
					options: 'Cost Center', fieldname: 'cost_center',
					filters: {'company': frm.doc.company}
				},
			]
		});
	},

	// show_redeposit_dialog: function(frm) {
	// 	const dialog = frm.events.get_journal_dialog(frm);
	// 	dialog.set_primary_action(__('Make'), function() {
	// 		const data = dialog.get_values();
	// 		if(!data) return;

	// 		data.voucher_type = 'Bank Entry';
	// 		data.company = frm.doc.company;
	// 		data.debit_account = frm.doc.paid_to;
	// 		data.credit_account = frm.doc.paid_from;
	// 		data.party = frm.doc.party;
	// 		data.party_type = frm.doc.party_type;
	// 		data.paid_amount = frm.doc.paid_amount;
	// 		data.payment_entry = frm.doc.name;
	// 		data.payment_entry_date = frm.doc.posting_date;

	// 		frappe.call({
	// 			method:"erpnext.accounts.utils.make_journal_entry",
	// 			args: {'args': data},
	// 			callback: function(r) {
	// 				dialog.hide();
	// 				if(r.message) {
	// 					frappe.set_route("Form", 'Journal Entry', r.message);
	// 				}
	// 			}
	// 		});
	// 	});

	// 	dialog.show();
	// },

	show_return_journal_dialog: function(frm) {
		const dialog = frm.events.get_journal_dialog(frm);

		dialog.set_primary_action(__('Make'), function() {
			const data = dialog.get_values();
			if(!data) return;

			data.voucher_type = 'Contra Entry';
			data.company = frm.doc.company;
			if(data.payment_type === 'Receive'){
				data.debit_account = frm.doc.paid_from;
				data.credit_account = frm.doc.paid_to;
			}
			else{
				data.debit_account = frm.doc.paid_to;
				data.credit_account = frm.doc.paid_from;
			}
			data.party = frm.doc.party;
			data.party_type = frm.doc.party_type;
			data.paid_amount = frm.doc.paid_amount;
			data.payment_entry = frm.doc.name;
			data.payment_entry_date = frm.doc.posting_date;
			data.payment_type = frm.doc.payment_type;
			console.log(data);
			frappe.call({
				method:"erpnext.accounts.utils.make_journal_entry",
				args: {'args': data},
				callback: function(r) {
					dialog.hide();
					if(r.message) {
						frappe.set_route("Form", 'Journal Entry', r.message);
					}
				}
			});
		});

		dialog.show();
	},


	company: function(frm) {
		frm.events.hide_unhide_fields(frm);
		frm.events.set_dynamic_labels(frm);
	},

	hide_unhide_fields: function(frm) {
		var company_currency = frm.doc.company? frappe.get_doc(":Company", frm.doc.company).default_currency: "";

		frm.toggle_display("source_exchange_rate",
			(frm.doc.paid_amount && frm.doc.paid_from_account_currency != company_currency));

		frm.toggle_display("target_exchange_rate", (frm.doc.received_amount &&
			frm.doc.paid_to_account_currency != company_currency &&
			frm.doc.paid_from_account_currency != frm.doc.paid_to_account_currency));

		frm.toggle_display("base_paid_amount", frm.doc.paid_from_account_currency != company_currency);

		frm.toggle_display("base_received_amount", (frm.doc.paid_to_account_currency != company_currency &&
			frm.doc.paid_from_account_currency != frm.doc.paid_to_account_currency));

		frm.toggle_display("received_amount", (frm.doc.payment_type=="Internal Transfer" ||
			frm.doc.paid_from_account_currency != frm.doc.paid_to_account_currency))

		frm.toggle_display(["base_total_allocated_amount"],
			(frm.doc.paid_amount && frm.doc.received_amount && frm.doc.base_total_allocated_amount &&
			((frm.doc.payment_type=="Receive" && frm.doc.paid_from_account_currency != company_currency) ||
			(frm.doc.payment_type=="Pay" && frm.doc.paid_to_account_currency != company_currency))));

		var party_amount = frm.doc.payment_type=="Receive" ?
			frm.doc.paid_amount : frm.doc.received_amount;

		frm.toggle_display("write_off_difference_amount", (frm.doc.difference_amount && frm.doc.party &&
			(frm.doc.paid_from_account_currency == frm.doc.paid_to_account_currency) &&
			(frm.doc.total_allocated_amount > party_amount)));

		frm.toggle_display("set_exchange_gain_loss",
			(frm.doc.paid_amount && frm.doc.received_amount && frm.doc.difference_amount &&
				(frm.doc.paid_from_account_currency != company_currency ||
					frm.doc.paid_to_account_currency != company_currency)));

		frm.refresh_fields();
	},

	set_dynamic_labels: function(frm) {
		var company_currency = frm.doc.company? frappe.get_doc(":Company", frm.doc.company).default_currency: "";

		frm.set_currency_labels(["base_paid_amount", "base_received_amount", "base_total_allocated_amount",
			"difference_amount"], company_currency);

		frm.set_currency_labels(["paid_amount"], frm.doc.paid_from_account_currency);
		frm.set_currency_labels(["received_amount"], frm.doc.paid_to_account_currency);

		var party_account_currency = frm.doc.payment_type=="Receive" ?
			frm.doc.paid_from_account_currency : frm.doc.paid_to_account_currency;

		frm.set_currency_labels(["total_allocated_amount", "unallocated_amount"], party_account_currency);

		var currency_field = (frm.doc.payment_type=="Receive") ? "paid_from_account_currency" : "paid_to_account_currency"
		frm.set_df_property("total_allocated_amount", "options", currency_field);
		frm.set_df_property("unallocated_amount", "options", currency_field);

		frm.set_currency_labels(["total_amount", "outstanding_amount", "allocated_amount"],
			party_account_currency, "references");

		frm.set_currency_labels(["amount"], company_currency, "deductions");

		cur_frm.set_df_property("source_exchange_rate", "description",
			("1 " + frm.doc.paid_from_account_currency + " = [?] " + company_currency));

		cur_frm.set_df_property("target_exchange_rate", "description",
			("1 " + frm.doc.paid_to_account_currency + " = [?] " + company_currency));

		frm.refresh_fields();
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
		
			if (in_list(frappe.user_roles, "Accounts Manager") && ! frm.doc.is_canceled)
				{
					frm.add_custom_button(__('Revarse'), function() {
					frappe.model.open_mapped_doc({
						method: "erpnext.accounts.doctype.payment_entry.payment_entry.make_reverse",
						frm: frm
					});
					}, "fa fa-table");
				}
		
		}
	},

	payment_type: function(frm) {
		if(frm.doc.payment_type == "Internal Transfer") {
			$.each(["party", "party_balance", "paid_from", "paid_to",
				"references", "total_allocated_amount"], function(i, field) {
					frm.set_value(field, null);
			})
		} else {
			if(!frm.doc.party)
				frm.set_value("party_type", frm.doc.payment_type=="Receive" ? "Customer" : "Supplier");
			else
				frm.events.party(frm);

			if(frm.doc.mode_of_payment)
				frm.events.mode_of_payment(frm);
		}
	},

	party_type: function(frm) {
		frm.set_value("party", "");
		frm.set_value("party_name", "");

		if(frm.doc.party) {
			$.each(["party", "party_balance", "paid_from", "paid_to",
				"paid_from_account_currency", "paid_from_account_balance",
				"paid_to_account_currency", "paid_to_account_balance",
				"references", "total_allocated_amount"], function(i, field) {
					frm.set_value(field, null);
			})
		}
	},

	party: function(frm) {

		if (frm.doc.party_type=='Customer'){
			frm.set_value("party_name", "");
			frm.set_value("party_name", frm.doc.party);
		}else if(frm.doc.party_type=='Supplier'){
			frm.set_value("party_name", "");
			frm.set_value("party_name", frm.doc.party);
		}


		if(frm.doc.payment_type && frm.doc.party_type && frm.doc.party) {
			if(!frm.doc.posting_date) {
				frappe.msgprint(__("Please select Posting Date before selecting Party"))
				frm.set_value("party", "");
				return ;
			}
			
			frm.set_party_account_based_on_party = true;

			return frappe.call({
				method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_party_details",
				args: {
					company: frm.doc.company,
					party_type: frm.doc.party_type,
					party: frm.doc.party,
					date: frm.doc.posting_date,
					payment_type: frm.doc.payment_type
				},
				callback: function(r, rt) {
					if(r.message) {
						if(frm.doc.payment_type == "Receive") {
							frm.set_value("paid_from", r.message.party_account);
							frm.set_value("paid_from_account_currency", r.message.party_account_currency);
							frm.set_value("paid_from_account_balance", r.message.account_balance);
						} else if (frm.doc.payment_type == "Pay"){
							frm.set_value("paid_to", r.message.party_account);
							frm.set_value("paid_to_account_currency", r.message.party_account_currency);
							frm.set_value("paid_to_account_balance", r.message.account_balance);
						}
						frm.set_value("party_balance", r.message.party_balance);
						frm.events.get_outstanding_documents(frm);
						frm.events.hide_unhide_fields(frm);
						frm.events.set_dynamic_labels(frm);
						frm.set_party_account_based_on_party = false;
					}
				}
			});
		}
	},

	paid_from: function(frm) {

		var is_bank = ''
		
		frappe.call({
		    method:"frappe.client.get_value", 
		     args:{
		     	doctype:'Account',

				fieldname:'account_type',
				filters:{'name': frm.doc.paid_from}
				},//dotted path to server method
		    callback: function(r) {
		        // code snippet
		        //alert(""+r.message)
		        if (r.message){
		        	console.log(r.message.account_type);
		        	is_bank = r.message.account_type;
		        	if (is_bank=='Bank'){
		        		f();

		        	}else{

		        		clean();
		        	}
		        }
		    }
		});
 
 var clean = function(){
	cur_frm.set_value("account_paid_from_name","");
	cur_frm.set_value("account_paid_from_no","");

};

 var f = function(){
		frappe.call({
		    method:"frappe.client.get_value", 
		     args:{
		     	doctype:'Bank Account',
				fieldname:'parent',
				filters:{'bank_account': frm.doc.paid_from}
				},//dotted path to server method
		    callback: function(r) {
		        // code snippet
		        //alert(""+r.message)
		        if (r.message){
		        	console.log(r.message.parent);
		        	cur_frm.set_value("account_paid_from_name",r.message.parent);

		        }
		    }
		});
	

		frappe.call({
		    method:"frappe.client.get_value", 
		     args:{
		     	doctype:'Bank Account',
				fieldname:'bank_account_no',
				filters:{'bank_account': String(cur_frm.doc.paid_from)}
				},//dotted path to server method
		    callback: function(r) {
		        // code snippet
		        //alert(""+r.message)
		        if (r.message){
		        	console.log(r.message.bank_account_no);
		        	cur_frm.set_value("account_paid_from_no",r.message.bank_account_no);

		        }
		    }
		});


};



		if(frm.set_party_account_based_on_party) return;

		frm.events.set_account_currency_and_balance(frm, frm.doc.paid_from,
			"paid_from_account_currency", "paid_from_account_balance", function(frm) {
				if (frm.doc.payment_type == "Receive") {
					frm.events.get_outstanding_documents(frm);
				} else if (frm.doc.payment_type == "Pay") {
					frm.events.paid_amount(frm);
				}
			}
		);
	},

	paid_to: function(frm) {

		
		

		var is_bank = ''
		
		frappe.call({
		    method:"frappe.client.get_value", 
		     args:{
		     	doctype:'Account',

				fieldname:'account_type',
				filters:{'name': frm.doc.paid_to}
				},//dotted path to server method
		    callback: function(r) {
		        // code snippet
		        //alert(""+r.message)
		        if (r.message){
		        	console.log(r.message.account_type);
		        	is_bank = r.message.account_type;
		        	if (is_bank=='Bank'){
		        		f();

		        	}else{

		        		clean();
		        	}
		        }
		    }
		});
 
 var clean = function(){
		        	cur_frm.set_value("account_paid_to_name","");
		        	cur_frm.set_value("account_paid_to_no","");

};

 var f = function(){
		frappe.call({
		    method:"frappe.client.get_value", 
		     args:{
		     	doctype:'Bank Account',
				fieldname:'parent',
				filters:{'bank_account': frm.doc.paid_to}
				},//dotted path to server method
		    callback: function(r) {
		        // code snippet
		        //alert(""+r.message)
		        if (r.message){
		        	console.log(r.message.parent);
		        	cur_frm.set_value("account_paid_to_name",r.message.parent);

		        }
		    }
		});
	

		frappe.call({
		    method:"frappe.client.get_value", 
		     args:{
		     	doctype:'Bank Account',
				fieldname:'bank_account_no',
				filters:{'bank_account': String(cur_frm.doc.paid_to)}
				},//dotted path to server method
		    callback: function(r) {
		        // code snippet
		        //alert(""+r.message)
		        if (r.message){
		        	console.log(r.message.bank_account_no);
		        	cur_frm.set_value("account_paid_to_no",r.message.bank_account_no);

		        }
		    }
		});


};



		if(frm.set_party_account_based_on_party) return;

		frm.events.set_account_currency_and_balance(frm, frm.doc.paid_to,
			"paid_to_account_currency", "paid_to_account_balance", function(frm) {
				if(frm.doc.payment_type == "Pay") {
					frm.events.get_outstanding_documents(frm);
				} else if (frm.doc.payment_type == "Receive") {
					frm.events.received_amount(frm);
				}
			}
		);
	},

	set_account_currency_and_balance: function(frm, account, currency_field,
			balance_field, callback_function) {
		if (account)
		frappe.call({
			method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_account_details",
			args: {
				"account": account,
				"date": frm.doc.posting_date
			},
			callback: function(r, rt) {
				if(r.message) {
					frm.set_value(currency_field, r.message['account_currency']);
					frm.set_value(balance_field, r.message['account_balance']);

					if(frm.doc.payment_type=="Receive" && currency_field=="paid_to_account_currency") {
						frm.toggle_reqd(["reference_no", "reference_date"],
							(r.message['account_type'] == "Bank" ? 1 : 0));
						if(!frm.doc.received_amount && frm.doc.paid_amount)
							frm.events.paid_amount(frm);
					} else if(frm.doc.payment_type=="Pay" && currency_field=="paid_from_account_currency") {
						frm.toggle_reqd(["reference_no", "reference_date"],
							(r.message['account_type'] == "Bank" ? 1 : 0));

						if(!frm.doc.paid_amount && frm.doc.received_amount)
							frm.events.received_amount(frm);
					}

					if(callback_function) callback_function(frm);

					frm.events.hide_unhide_fields(frm);
					frm.events.set_dynamic_labels(frm);
				}
			}
		});
	},

	paid_from_account_currency: function(frm) {
		if(!frm.doc.paid_from_account_currency) return;
		var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;

		if (frm.doc.paid_from_account_currency == company_currency) {
			frm.set_value("source_exchange_rate", 1);
		} else if (frm.doc.paid_from){
			if (in_list(["Internal Transfer", "Pay"], frm.doc.payment_type)) {
				frappe.call({
					method: "erpnext.accounts.doctype.journal_entry.journal_entry.get_average_exchange_rate",
					args: {
						account: frm.doc.paid_from
					},
					callback: function(r, rt) {
						frm.set_value("source_exchange_rate", r.message);
					}
				})
			} else {
				frm.events.set_current_exchange_rate(frm, "source_exchange_rate",
					frm.doc.paid_from_account_currency, company_currency);
			}
		}
	},

	paid_to_account_currency: function(frm) {
		if(!frm.doc.paid_to_account_currency) return;
		var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;

		frm.events.set_current_exchange_rate(frm, "target_exchange_rate",
			frm.doc.paid_to_account_currency, company_currency);
	},

	set_current_exchange_rate: function(frm, exchange_rate_field, from_currency, to_currency) {
		frappe.call({
			method: "erpnext.setup.utils.get_exchange_rate",
			args: {
				transaction_date: frm.doc.posting_date,
				from_currency: from_currency,
				to_currency: to_currency
			},
			callback: function(r, rt) {
				frm.set_value(exchange_rate_field, r.message);
			}
		})
	},
	
	posting_date: function(frm) {
		frm.events.paid_from_account_currency(frm);
	},

	source_exchange_rate: function(frm) {
		if (frm.doc.paid_amount) {
			frm.set_value("base_paid_amount", flt(frm.doc.paid_amount) * flt(frm.doc.source_exchange_rate));
			if(!frm.set_paid_amount_based_on_received_amount &&
					(frm.doc.paid_from_account_currency == frm.doc.paid_to_account_currency)) {
				frm.set_value("target_exchange_rate", frm.doc.source_exchange_rate);
				frm.set_value("base_received_amount", frm.doc.base_paid_amount);
			}
			
			frm.events.set_difference_amount(frm);
		}
	},

	target_exchange_rate: function(frm) {
		frm.set_paid_amount_based_on_received_amount = true;
		
		if (frm.doc.received_amount) {
			frm.set_value("base_received_amount",
				flt(frm.doc.received_amount) * flt(frm.doc.target_exchange_rate));
				
			if(!frm.doc.source_exchange_rate && 
					(frm.doc.paid_from_account_currency == frm.doc.paid_to_account_currency)) {
				frm.set_value("source_exchange_rate", frm.doc.target_exchange_rate);
				frm.set_value("base_paid_amount", frm.doc.base_received_amount);
			}
			
			frm.events.set_difference_amount(frm);
		}
		frm.set_paid_amount_based_on_received_amount = false;
	},

	paid_amount: function(frm) {
		frm.set_value("base_paid_amount", flt(frm.doc.paid_amount) * flt(frm.doc.source_exchange_rate));
		frm.trigger("reset_received_amount");
	},

	received_amount: function(frm) {
		frm.set_paid_amount_based_on_received_amount = true;

		if(!frm.doc.paid_amount && frm.doc.paid_from_account_currency == frm.doc.paid_to_account_currency) {
			frm.set_value("paid_amount", frm.doc.received_amount);

			if(frm.doc.target_exchange_rate) {
				frm.set_value("source_exchange_rate", frm.doc.target_exchange_rate);
			}
			frm.set_value("base_paid_amount", frm.doc.base_received_amount);
		}

		frm.set_value("base_received_amount",
			flt(frm.doc.received_amount) * flt(frm.doc.target_exchange_rate));

		if(frm.doc.payment_type == "Pay")
			frm.events.allocate_party_amount_against_ref_docs(frm, frm.doc.received_amount);
		else
			frm.events.set_difference_amount(frm);
		
		frm.set_paid_amount_based_on_received_amount = false;
	},
	
	reset_received_amount: function(frm) {
		if(!frm.set_paid_amount_based_on_received_amount &&
				(frm.doc.paid_from_account_currency == frm.doc.paid_to_account_currency)) {
			
			frm.set_value("received_amount", frm.doc.paid_amount);

			if(frm.doc.source_exchange_rate) {
				frm.set_value("target_exchange_rate", frm.doc.source_exchange_rate);
			}
			frm.set_value("base_received_amount", frm.doc.base_paid_amount);
		}
		
		if(frm.doc.payment_type == "Receive")
			frm.events.allocate_party_amount_against_ref_docs(frm, frm.doc.paid_amount);
		else
			frm.events.set_difference_amount(frm);
	},

	get_outstanding_documents: function(frm) {
		frm.clear_table("references");

		if(!frm.doc.party) return;

		frm.events.check_mandatory_to_fetch(frm);
		var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;

		return  frappe.call({
			method: 'erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents',
			args: {
				args: {
					"posting_date": frm.doc.posting_date,
					"company": frm.doc.company,
					"party_type": frm.doc.party_type,
					"payment_type": frm.doc.payment_type,
					"party": frm.doc.party,
					"party_account": frm.doc.payment_type=="Receive" ? frm.doc.paid_from : frm.doc.paid_to
				}
			},
			callback: function(r, rt) {
				if(r.message) {
					var total_positive_outstanding = 0;
					var total_negative_outstanding = 0;

					$.each(r.message, function(i, d) {
						var c = frm.add_child("references");
						c.reference_doctype = d.voucher_type;
						c.reference_name = d.voucher_no;
						c.total_amount = d.invoice_amount;
						c.outstanding_amount = d.outstanding_amount;
						if(!in_list(["Sales Order", "Purchase Order"], d.voucher_type)) {
							if(flt(d.outstanding_amount) > 0)
								total_positive_outstanding += flt(d.outstanding_amount);
							else
								total_negative_outstanding += Math.abs(flt(d.outstanding_amount));
						}

						var party_account_currency = frm.doc.payment_type=="Receive" ?
							frm.doc.paid_from_account_currency : frm.doc.paid_to_account_currency;

						if(party_account_currency != company_currency) {
							c.exchange_rate = d.exchange_rate;
						} else {
							c.exchange_rate = 1;
						}
						if (in_list(['Sales Invoice', 'Purchase Invoice'], d.reference_doctype)){
							c.due_date = d.due_date;
						}
					});

					if((frm.doc.payment_type=="Receive" && frm.doc.party_type=="Customer") ||
						(frm.doc.payment_type=="Pay" && frm.doc.party_type=="Supplier")) {
							if(total_positive_outstanding > total_negative_outstanding)
								frm.set_value("paid_amount",
									total_positive_outstanding - total_negative_outstanding);
					} else if (total_negative_outstanding &&
							(total_positive_outstanding < total_negative_outstanding)) {
						frm.set_value("received_amount",
							total_negative_outstanding - total_positive_outstanding);
					}
				}

				frm.events.allocate_party_amount_against_ref_docs(frm,
					(frm.doc.payment_type=="Receive" ? frm.doc.paid_amount : frm.doc.received_amount));
			}
		});
	},

	allocate_payment_amount: function(frm) {
		if(frm.doc.payment_type == 'Internal Transfer'){
			return
		}

		if(frm.doc.references.length == 0){
			frm.events.get_outstanding_documents(frm);
		}

		frm.events.allocate_party_amount_against_ref_docs(frm, frm.doc.received_amount);
	},

	allocate_party_amount_against_ref_docs: function(frm, paid_amount) {
		var total_positive_outstanding_including_order = 0;
		var total_negative_outstanding = 0;

		$.each(frm.doc.references || [], function(i, row) {
			if(flt(row.outstanding_amount) > 0)
				total_positive_outstanding_including_order += flt(row.outstanding_amount);
			else
				total_negative_outstanding += Math.abs(flt(row.outstanding_amount));
		})

		var allocated_negative_outstanding = 0;
		if((frm.doc.payment_type=="Receive" && frm.doc.party_type=="Customer") ||
				(frm.doc.payment_type=="Pay" && frm.doc.party_type=="Supplier")) {
			if(total_positive_outstanding_including_order > paid_amount) {
				var remaining_outstanding = total_positive_outstanding_including_order - paid_amount;
				allocated_negative_outstanding = total_negative_outstanding < remaining_outstanding ?
					total_negative_outstanding : remaining_outstanding;
			}

			var allocated_positive_outstanding =  paid_amount + allocated_negative_outstanding;
		} else {
			if(paid_amount > total_negative_outstanding) {
				if(total_negative_outstanding == 0) {
					frappe.msgprint(__("Cannot {0} {1} {2} without any negative outstanding invoice",
						[frm.doc.payment_type,
							(frm.doc.party_type=="Customer" ? "to" : "from"), frm.doc.party_type]));
					return false
				} else {
					frappe.msgprint(__("Paid Amount cannot be greater than total negative outstanding amount {0}", [total_negative_outstanding]));
					return false;
				}
			} else {
				allocated_positive_outstanding = total_negative_outstanding - paid_amount;
				allocated_negative_outstanding = paid_amount +
					(total_positive_outstanding_including_order < allocated_positive_outstanding ?
						total_positive_outstanding_including_order : allocated_positive_outstanding)
			}
		}

		$.each(frm.doc.references || [], function(i, row) {
			row.allocated_amount = 0 //If allocate payment amount checkbox is unchecked, set zero to allocate amount
			if(frm.doc.allocate_payment_amount){
				if(row.outstanding_amount > 0 && allocated_positive_outstanding > 0) {
					if(row.outstanding_amount >= allocated_positive_outstanding)
							row.allocated_amount = allocated_positive_outstanding;
					else row.allocated_amount = row.outstanding_amount;

					allocated_positive_outstanding -= flt(row.allocated_amount);
				} else if (row.outstanding_amount < 0 && allocated_negative_outstanding) {
					if(Math.abs(row.outstanding_amount) >= allocated_negative_outstanding)
						row.allocated_amount = -1*allocated_negative_outstanding;
					else row.allocated_amount = row.outstanding_amount;

					allocated_negative_outstanding -= Math.abs(flt(row.allocated_amount));
				}
			}
		})

		frm.refresh_fields()
		frm.events.set_total_allocated_amount(frm);
	},

	set_total_allocated_amount: function(frm) {
		var total_allocated_amount = base_total_allocated_amount = 0.0;
		$.each(frm.doc.references || [], function(i, row) {
			if (row.allocated_amount) {
				total_allocated_amount += flt(row.allocated_amount);
				base_total_allocated_amount += flt(flt(row.allocated_amount)*flt(row.exchange_rate),
					precision("base_paid_amount"));
			}
		});
		frm.set_value("total_allocated_amount", Math.abs(total_allocated_amount));
		frm.set_value("base_total_allocated_amount", Math.abs(base_total_allocated_amount));

		frm.events.set_difference_amount(frm);
	},

	set_difference_amount: function(frm) {
		var unallocated_amount = 0;
		if(frm.doc.party) {
			var party_amount = frm.doc.payment_type=="Receive" ?
				frm.doc.paid_amount : frm.doc.received_amount;
				
			var total_deductions = frappe.utils.sum($.map(frm.doc.deductions || [],
				function(d) { return flt(d.amount) }));

			if(frm.doc.total_allocated_amount < party_amount) {
				if(frm.doc.payment_type == "Receive") {
					unallocated_amount = party_amount - (frm.doc.total_allocated_amount - total_deductions);
				} else {
					unallocated_amount = party_amount - (frm.doc.total_allocated_amount + total_deductions);
				}
			}
		}
		frm.set_value("unallocated_amount", unallocated_amount);

		var difference_amount = 0;
		var base_unallocated_amount = flt(frm.doc.unallocated_amount) *
			(frm.doc.payment_type=="Receive" ? frm.doc.source_exchange_rate : frm.doc.target_exchange_rate);

		var base_party_amount = flt(frm.doc.base_total_allocated_amount) + base_unallocated_amount;

		if(frm.doc.payment_type == "Receive") {
			difference_amount = base_party_amount - flt(frm.doc.base_received_amount);
		} else if (frm.doc.payment_type == "Pay") {
			difference_amount = flt(frm.doc.base_paid_amount) - base_party_amount;
		} else {
			difference_amount = flt(frm.doc.base_paid_amount) - flt(frm.doc.base_received_amount);
		}

		$.each(frm.doc.deductions || [], function(i, d) {
			if(d.amount) difference_amount -= flt(d.amount);
		})

		frm.set_value("difference_amount", difference_amount);

		frm.events.hide_unhide_fields(frm);
	},

	check_mandatory_to_fetch: function(frm) {
		$.each(["Company", "Party Type", "Party", "payment_type"], function(i, field) {
			if(!frm.doc[frappe.model.scrub(field)]) {
				frappe.msgprint(__("Please select {0} first", [field]));
				return false;
			}

		});
	},

	validate_reference_document: function(frm, row) {
		var _validate = function(i, row) {
			if (!row.reference_doctype) {
				return;
			}

			if(frm.doc.party_type=="Customer"
				&& !in_list(["Sales Order", "Sales Invoice", "Journal Entry"], row.reference_doctype)) {
					frappe.model.set_value(row.doctype, row.name, "reference_doctype", null);
					frappe.msgprint(__("Row #{0}: Reference Document Type must be one of Sales Order, Sales Invoice or Journal Entry", [row.idx]));
					return false;
				}

			if(frm.doc.party_type=="Supplier" && !in_list(["Purchase Order",
				"Purchase Invoice", "Journal Entry"], row.reference_doctype)) {
					frappe.model.set_value(row.doctype, row.name, "against_voucher_type", null);
					frappe.msgprint(__("Row #{0}: Reference Document Type must be one of Purchase Order, Purchase Invoice or Journal Entry", [row.idx]));
					return false;
				}
		}

		if (row) {
			_validate(0, row);
		} else {
			$.each(frm.doc.vouchers || [], _validate);
		}
	},

	write_off_difference_amount: function(frm) {
		frm.events.set_deductions_entry(frm, "write_off_account");
	},

	set_exchange_gain_loss: function(frm) {
		frm.events.set_deductions_entry(frm, "exchange_gain_loss_account");
	},

	set_deductions_entry: function(frm, account) {
		if(frm.doc.difference_amount) {
			frappe.call({
				method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_company_defaults",
				args: {
					company: frm.doc.company
				},
				callback: function(r, rt) {
					if(r.message) {
						var write_off_row = $.map(frm.doc["deductions"] || [], function(t) {
							return t.account==r.message[account] ? t : null; });

						if (!write_off_row.length) {
							var row = frm.add_child("deductions");
							row.account = r.message[account];
							row.cost_center = r.message["cost_center"];
						} else {
							var row = write_off_row[0];
						}

						row.amount = flt(row.amount) + flt(frm.doc.difference_amount);
						refresh_field("deductions");

						frm.events.set_difference_amount(frm);
					}
				}
			})
		}
	}
});


frappe.ui.form.on('Payment Entry Reference', {
	reference_doctype: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frm.events.validate_reference_document(frm, row);
	},

	reference_name: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		return frappe.call({
			method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_reference_details",
			args: {
				reference_doctype: row.reference_doctype,
				reference_name: row.reference_name,
				party_account_currency: frm.doc.payment_type=="Receive" ?
					frm.doc.paid_from_account_currency : frm.doc.paid_to_account_currency
			},
			callback: function(r, rt) {
				if(r.message) {
					$.each(r.message, function(field, value) {
						frappe.model.set_value(cdt, cdn, field, value);
					})
					frm.refresh_fields();
				}
			}
		})
	},

	allocated_amount: function(frm) {
		frm.events.set_total_allocated_amount(frm);
	},

	references_remove: function(frm) {
		frm.events.set_total_allocated_amount(frm);
	}
})

frappe.ui.form.on('Payment Entry Deduction', {
	amount: function(frm) {
		frm.events.set_difference_amount(frm);
	},

	deductions_remove: function(frm) {
		frm.events.set_difference_amount(frm);
	}
})
