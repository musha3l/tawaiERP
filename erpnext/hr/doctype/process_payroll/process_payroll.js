// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
cur_frm.add_fetch('company', 'cost_center', 'payroll_cost_center');

frappe.ui.form.on("Process Payroll", {
	onload: function(frm) {
		erpnext.process_payroll.load_employees(frm);
		frm.doc.posting_date = frappe.datetime.nowdate();
		frm.doc.start_date = '';
		frm.doc.end_date = '';
		frm.doc.payroll_frequency = '';
		frm.toggle_reqd(['payroll_frequency'], !frm.doc.salary_slip_based_on_timesheet);
		frm.refresh_field("posting_date");
	},

	setup: function(frm) {
		frm.set_query("payment_account", function() {
			var account_types = ["Bank", "Cash"];
			return {
				filters: {
					"account_type": ["in", account_types],
					"is_group": 0,
					"company": frm.doc.company
				}
			}
		})
	},

	refresh: function(frm) {
		frm.disable_save();
	},

	payroll_frequency: function(frm) {
		frm.trigger("set_start_end_dates");
	},

	start_date: function(frm) {
		erpnext.process_payroll.load_employees(frm);
	},

	end_date: function(frm) {
		erpnext.process_payroll.load_employees(frm);
	},

	department: function(frm) {
		erpnext.process_payroll.load_employees(frm);
	},

	branch: function(frm) {
		erpnext.process_payroll.load_employees(frm);
	},

	salary_slip_based_on_timesheet: function(frm) {
		frm.toggle_reqd(['payroll_frequency'], !frm.doc.salary_slip_based_on_timesheet);
	},

	payment_account: function(frm) {
		frm.toggle_display(['make_bank_entry'], (frm.doc.payment_account!="" && frm.doc.payment_account!="undefined"));
		//~ frm.toggle_display(['cost_center'], (frm.doc.payment_account!="" && frm.doc.payment_account!="undefined"));
	},

	set_start_end_dates: function(frm) {
		if (!frm.doc.salary_slip_based_on_timesheet){
			frappe.call({
				method:'erpnext.hr.doctype.process_payroll.process_payroll.get_start_end_dates',
				args:{
					payroll_frequency: frm.doc.payroll_frequency,
					start_date: frm.doc.start_date || frm.doc.posting_date
				},
				callback: function(r){
					if (r.message){
						frm.set_value('start_date', r.message.start_date);
						frm.set_value('end_date', r.message.end_date);
					}
				}
			})
		}
	}
})

erpnext.process_payroll = {
	load_employees: function(frm) {
		if((frm.doc.start_date) && (frm.doc.end_date)) {
			frappe.call({
				method: "erpnext.hr.doctype.process_payroll.process_payroll.get_employees",
				args: {
					start_date: frm.doc.start_date,
					end_date: frm.doc.end_date,
					department: frm.doc.department,
					branch: frm.doc.branch,
					company: frm.doc.company
				},
				callback: function(r) {
					if(r.message['unmarked'].length > 0) {
						unhide_field('unmarked_email_salary_slip')
						if(!frm.employee_area) {
							frm.employee_area = $('<div>')
							.appendTo(frm.fields_dict.employees_html.wrapper);
						}
						frm.EmployeeSelector = new erpnext.EmployeeSelector(frm, frm.employee_area, r.message['unmarked'])
					}
					else{
						hide_field('unmarked_email_salary_slip')
					}

					if(r.message['marked'].length > 0) {
						unhide_field('marked_email_salary_slip_html')
						if(!frm.marked_employee_area) {
							frm.marked_employee_area = $('<div>')
								.appendTo(frm.fields_dict.marked_email_salary_slip_html.wrapper);
						}
						frm.marked_employee = new erpnext.MarkedEmployee(frm, frm.marked_employee_area, r.message['marked'])
					}
					else{
						hide_field('marked_email_salary_slip_html')
					}
				}
			});
		}
	}
}

cur_frm.cscript.display_activity_log = function(msg) {
	if(!cur_frm.ss_html)
		cur_frm.ss_html = $a(cur_frm.fields_dict['activity_log'].wrapper,'div');
	if(msg) {
		cur_frm.ss_html.innerHTML =
			'<div class="padding"><h4>'+__("Activity Log:")+'</h4>'+msg+'</div>';
	} else {
		cur_frm.ss_html.innerHTML = "";
	}
}

//Create salary slip
//-----------------------
cur_frm.cscript.create_salary_slip = function(doc, cdt, cdn) {
	cur_frm.cscript.display_activity_log("");
	var callback = function(r, rt){
		if (r.message)
			cur_frm.cscript.display_activity_log(r.message);
	}
	return $c('runserverobj', args={'method':'create_salary_slips','docs':doc},callback);
}

cur_frm.cscript.submit_salary_slip = function(doc, cdt, cdn) {
	cur_frm.cscript.display_activity_log("");

	frappe.confirm(__("Do you really want to Submit all Salary Slip from {0} to {1}", [doc.start_date, doc.end_date]), function() {
		// clear all in locals
		if(locals["Salary Slip"]) {
			$.each(locals["Salary Slip"], function(name, d) {
				frappe.model.remove_from_locals("Salary Slip", name);
			});
		}

		var callback = function(r, rt){
			if (r.message)
				cur_frm.cscript.display_activity_log(r.message);
		}

		return $c('runserverobj', args={'method':'submit_salary_slips','docs':doc},callback);
	});
}

cur_frm.cscript.make_bank_entry = function(doc,cdt,cdn){
    if(doc.company && doc.start_date && doc.end_date){
		return cur_frm.cscript.reference_entry(doc,cdt,cdn);
    } else {
  	  msgprint(__("Company, From Date and To Date is mandatory"));
    }
}

cur_frm.cscript.reference_entry = function(doc,cdt,cdn){
	var dialog = new frappe.ui.Dialog({
		title: __("Bank Transaction Reference"),
		fields: [
			{
				"label": __("Reference Number"),
				"fieldname": "reference_number",
				"fieldtype": "Data",
				"reqd": 1
			},
			{
				"label": __("Reference Date"),
				"fieldname": "reference_date",
				"fieldtype": "Date",
				"reqd": 1,
				"default": frappe.datetime.get_today()
			}
		]
	});
	dialog.set_primary_action(__("Make"), function() {
		args = dialog.get_values();
		if(!args) return;
		dialog.hide();
		return frappe.call({
			doc: cur_frm.doc,
			method: "make_journal_entry",
			args: {"reference_number": args.reference_number, "reference_date":args.reference_date},
			callback: function(r) {
				if (r.message)
					cur_frm.cscript.display_activity_log(r.message);
			}
		});
	});
	dialog.show();
}

erpnext.MarkedEmployee = Class.extend({
	init: function(frm, wrapper, employee) {
		this.wrapper = wrapper;
		this.frm = frm;
		this.make(frm, employee);
	},
	make: function(frm, employee) {
		var me = this;
		$(this.wrapper).empty();

		var row;
		$.each(employee, function(i, m) {
			var icon = "fa fa-check";
			var color_class = "";
			if(m.email_salary_slip == 1) {
				icon = "fa fa-check"
				color_class = "text-muted";
			}


			if (i===0 || i % 4===0) {
				row = $('<div class="row"></div>').appendTo(me.wrapper);
			}

			$(repl('<div class="col-sm-3 %(color_class)s">\
				<label class="marked-employee-label"><span class="%(icon)s"></span>\
				%(employee)s</label>\
				</div>', {
					employee: m.employee_name,
					icon: icon,
					color_class: color_class
				})).appendTo(row);
		});
	}
});

erpnext.EmployeeSelector = Class.extend({
	init: function(frm, wrapper, employee) {
		this.wrapper = wrapper;
		this.frm = frm;
		this.make(frm, employee);
	},
	make: function(frm, employee) {
		var me = this;

		$(this.wrapper).empty();
		var employee_toolbar = $('<div class="col-sm-12 top-toolbar">\
			<button class="btn btn-default btn-add btn-xs"></button>\
			<button class="btn btn-xs btn-default btn-remove"></button>\
			</div>').appendTo($(this.wrapper));

		var mark_employee_toolbar = $('<div class="col-sm-12 bottom-toolbar">\
			<button class="btn btn-primary btn-mark btn-xs"></button></div>')

		employee_toolbar.find(".btn-add")
			.html(__('Check all'))
			.on("click", function() {
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if(!$(check).is(":checked")) {
						check.checked = true;
					}
				});
			});

		employee_toolbar.find(".btn-remove")
			.html(__('Uncheck all'))
			.on("click", function() {
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if($(check).is(":checked")) {
						check.checked = false;
					}
				});
			});

		mark_employee_toolbar.find(".btn-mark")
			.html(__('Email Salary Slip'))
			.on("click", function() {
				frappe.confirm(__("Do you really want to Email Salary Slip to employee from {0} to {1}", [frm.doc.start_date, frm.doc.end_date]), function() {
				var employee_present = [];
				$(me.wrapper).find('input[type="checkbox"]').each(function(i, check) {
					if($(check).is(":checked")) {
						employee_present.push(employee[i]);
					}
				});
				frappe.call({
					method: "erpnext.hr.doctype.process_payroll.process_payroll.email_salary_slips",
					args:{
						"employee_list":employee_present,
						"start_date":frm.doc.start_date,
						"end_date":frm.doc.end_date
					},

					callback: function(r) {

						erpnext.process_payroll.load_employees(frm);

					}
				});
				});
			});



		var row;
		$.each(employee, function(i, m) {
			if (i===0 || (i % 4) === 0) {
				row = $('<div class="row"></div>').appendTo(me.wrapper);
			}

			$(repl('<div class="col-sm-3 unmarked-employee-checkbox">\
				<div class="checkbox">\
				<label><input type="checkbox" class="employee-check" employee="%(employee)s"/>\
				%(employee)s</label>\
				</div></div>', {employee: m.employee_name})).appendTo(row);
		});

		mark_employee_toolbar.appendTo($(this.wrapper));
	}
});
