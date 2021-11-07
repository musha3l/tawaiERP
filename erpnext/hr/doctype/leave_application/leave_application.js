// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

cur_frm.add_fetch('employee', 'employee_name', 'employee_name');
 cur_frm.add_fetch('employee', 'department', 'department');
cur_frm.add_fetch('employee', 'company', 'company');
// cur_frm.add_fetch('employee', 'reports_to', 'leave_approver');
// cur_frm.cscript.custom_leave_type = function(doc) {
//     if (cur_frm.doc.leave_type !== "Annual Leave - اجازة اعتيادية" && cur_frm.doc.leave_type !== "Compensatory off - تعويضية") {
//         cur_frm.set_df_property("monthly_accumulated_leave_balance", "hidden", 1);
//     } else {
//         cur_frm.set_df_property("monthly_accumulated_leave_balance", "hidden", 0);
//     }
// }
cur_frm.fields_dict.alternative_employee.get_query = function(doc) {
    if (cur_frm.doc.employee == undefined || cur_frm.doc.employee == "") {
        frappe.throw(__("Please select an employee"));
    }

    // if ('Director' in frappe.roles(user)) {
    //     // alert("hhh")
    //     return {
    //         filters: [
    //             ['status', '=', 'Active'],
    //             ['name', '!=', cur_frm.doc.employee]
    //         ]
    //     };
    // } else {
    //     // alert("mmm")
    //     if (frm.doc.__islocal) {
    //         return {
    //             filters: [
    //                 ['status', '=', 'Active'],
    //                 ['name', '!=', cur_frm.doc.employee],
    //                 ['department', '=', cur_frm.doc.department]
    //             ]

    //         };
    //     }
    // }
};
frappe.ui.form.on("Leave Application", {
    validate: function(frm) {
        // tit = frm.page.$title_area.find('.hidden-xs');
        // console.log(tit);
        // if (!frm.doc.__islocal && frm.doc.owner != frappe.session.user) {
        //     // if (frm.doc.leave_approver != frappe.session.user && frm.doc.docstatus != 1) {
        //     //     //~ frm.set_value("docstatus", 0);
        //     //     //     cur_frm.doc.docstatus = 0
        //     //     //     frm.set_value("workflow_state", "Pending");
        //     //     //     alert("Hit");
        //     //     // } else {
        //     //     //     alert("No");
        //     // }
        // }

    },
    onload: function(frm) {
        if (cur_frm.doc.__islocal) {
            frm.enable_save();
        }

        if (!frm.doc.posting_date) {
            frm.set_value("posting_date", frappe.datetime.get_today());
        }

        // frm.set_query("leave_approver", function() {
        //     return {
        //         query: "erpnext.hr.doctype.leave_application.leave_application.get_approvers",
        //         filters: {
        //             employee: frm.doc.employee
        //         }
        //     };
        // });

        frm.set_query("employee", erpnext.queries.employee);

    },

    refresh: function(frm) {
        if(!frm.doc.__islocal){
            frm.disable_save();
        }else{
            frm.enable_save();
        }
        
        frappe.call({
            method: "unallowed_actions",
            doc: frm.doc,
            freeze: true,
            callback: function(r) {
                if (r.message && frappe.session.user != "Administrator") {  
                    frm.page.clear_actions_menu();
                }
            }
        });
        if (!cur_frm.doc.__islocal) {
            frm.disable_save();
        }
        if (cur_frm.doc.leave_type != "Annual Leave - اجازة اعتيادية" && cur_frm.doc.leave_type != "Without Pay - غير مدفوعة" && cur_frm.doc.leave_type != "Compensatory off - تعويضية" && cur_frm.doc.leave_type != "emergency -اضطرارية") {
            // alert('dfggg');
            if (!cur_frm.doc.__islocal) {
                // alert("fgg");
                // cur_frm.set_df_property("attachment", "reqd", 1);
                // refresh_field("attachment");
            }
        } else {
            cur_frm.set_df_property("attachment", "reqd", 0);
            refresh_field("attachment");
        }
        frm.set_df_property("naming_series", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("leave_type", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("employee", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("from_date", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("to_date", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("description", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("alternative_employee", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("posting_date", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("company", "read_only", frm.doc.__islocal ? 0 : 1);
        frm.set_df_property("letter_head", "read_only", frm.doc.__islocal ? 0 : 1);






        if (frm.doc.docstatus == 1 && frm.doc.status != "Returned") {
            if (frm.doc.from_date <= frappe.datetime.get_today() && frm.doc.to_date >= frappe.datetime.get_today()) {
                frm.add_custom_button(__("Cancel Leave Application"), function() {
                    // frappe.route_options = { "integration_request_service": "Razorpay" };
                    frappe.route_options = {"leave_application":frm.docname}
                    frappe.set_route("Form", "Cancel Leave Application", "New Cancel Leave Application 1");

                });
            }
            if (frm.doc.to_date < frappe.datetime.get_today() && frm.doc.status == "Approved") {
                frm.add_custom_button(__("Return From Leave Statement"), function() {
                    // frappe.route_options = { "integration_request_service": "Razorpay" };
                    frappe.route_options = {"leave_application":frm.docname}
                    frappe.set_route("Form", "Return From Leave Statement", "New Return From Leave Statement 1");
                });
            }
        }else if (frm.doc.to_date > frappe.datetime.get_today() && frm.doc.docstatus === 1 && frm.doc.status === "Returned" && frm.doc.return_date < frm.doc.to_date ) {
      frm.add_custom_button(__("Resume Leave"), function() {
        frappe.confirm(
          __('Are you sure to Resume Leave Application Based on Today Date ?'),
          function(){
                        console.log(frappe.datetime.get_today())
                        console.log(frm.doc.return_date)
                        console.log( frappe.datetime.get_day_diff( frappe.datetime.get_today() , frm.doc.return_date) );

                        frappe.call({
                            method: 'erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days',
                            args: {
                                "employee": frm.doc.employee,
                                "leave_type": frm.doc.leave_type,
                                "from_date": frm.doc.from_date,
                                "to_date": frm.doc.return_date,
                                "half_day": frm.doc.half_day
                            },
                            callback: function(result1) {
                                if (result1 && result1.message) {
                                    frappe.call({
                                        method: 'erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days',
                                        args: {
                                            "employee": frm.doc.employee,
                                            "leave_type": frm.doc.leave_type,
                                            "from_date": frappe.datetime.get_today(),
                                            "to_date": frm.doc.to_date,
                                            "half_day": frm.doc.half_day
                                        },
                                        callback: function(result2) {
                                            if (result2 && result2.message) {
                                                console.log("Result")
                                                console.log( parseFloat(result1.message))
                                                console.log(parseFloat(result2.message))
                                                console.log(parseFloat(result1.message) +parseFloat(result2.message) - 1 )
                                                // frm.set_value('total_leave_days', parseFloat(result1.message) +parseFloat(result2.message)-1 );
                                                // frm.set_value('remaining_leave_days', parseFloat(frm.doc.leave_balance)   - parseFloat(r.message));
                    
                                                // frm.trigger("get_leave_balance");
                                                // frm.trigger("calculate_monthly_accumulated_leave");
                                            }
                                        }
                                    });
                                }
                            }
                        });

                        frappe.show_alert(__('Leave Application: ' + frm.doc.name + 'is now Resumed'))
          },
          function(){
                        frappe.prompt([
                            {'fieldname': 'resume_date', 'fieldtype': 'Date', 'label': 'Resuming Date', 'reqd': 1}  
                        ],
                        function(values){
                            console.log(values.resume_date)    
                            console.log(frappe.datetime.get_today())
                            console.log(frm.doc.return_date)
                            console.log( frappe.datetime.get_day_diff( values.resume_date , frm.doc.return_date) - 1 );
                            frappe.call({
                                method: 'erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days',
                                args: {
                                    "employee": frm.doc.employee,
                                    "leave_type": frm.doc.leave_type,
                                    "from_date": frm.doc.from_date,
                                    "to_date": frm.doc.return_date,
                                    "half_day": frm.doc.half_day
                                },
                                callback: function(result1) {
                                    if (result1 && result1.message) {
                                        frappe.call({
                                            method: 'erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days',
                                            args: {
                                                "employee": frm.doc.employee,
                                                "leave_type": frm.doc.leave_type,
                                                "from_date": values.resume_date,
                                                "to_date": frm.doc.to_date,
                                                "half_day": frm.doc.half_day
                                            },
                                            callback: function(result2) {
                                                if (result2 && result2.message) {
                                                    console.log("Result")
                                                    console.log( parseFloat(result1.message))
                                                    console.log(parseFloat(result2.message))
                                                    console.log(parseFloat(result1.message) +parseFloat(result2.message) - 1 )
                                                    frm.set_value('total_leave_days', parseFloat(result1.message) +parseFloat(result2.message)-1 );
                                                    frm.set_value('remaining_leave_days', parseFloat(frm.doc.leave_balance)-(parseFloat(result1.message) +parseFloat(result2.message)-1));
                        
                                                    frm.trigger("get_leave_balance");
                                                    // frm.trigger("calculate_monthly_accumulated_leave");
                                                    frappe.call({
                                                        method: 'erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days',
                                                        args: {
                                                            "employee": frm.doc.employee,
                                                            "leave_type": frm.doc.leave_type,
                                                            "from_date": frm.doc.return_date,
                                                            "to_date": values.resume_date,
                                                            "half_day": frm.doc.half_day
                                                        },
                                                        callback: function(result3) {
                                                            if (result3 && result3.message) {
                                                                // frm.set_value("monthly_accumulated_leave_balance",parseFloat(frm.doc.monthly_accumulated_leave_balance) + parseFloat(result3.message)-1 )

                                                            }
                                                        }
                                                    });
                                                }
                                            }
                                        });
                                    }
                                }
                            });
    
                            frappe.show_alert(__('Leave Application: ' + frm.doc.name + 'is now Resumed'))
                        },
                        'Resume Leave Date Verification',
                        'Submit'
                        )
            // frappe.show_alert('Thanks for continue here!')
          }
        )
        // frappe.route_options = {"leave_application":frm.docname}
        // frappe.set_route("Form", "Return From Leave Statement", "New Return From Leave Statement 1");
      });
    }
        if (frm.is_new()) {
            frm.set_value("status", "Open");
            frm.trigger("calculate_total_days");
        }

        // if (!frm.doc.__islocal && frm.doc.owner == frappe.session.user) {
        //     if (frm.doc.leave_type=="New Born - مولود جديد" ||  frm.doc.leave_type=="Death - وفاة" || frm.doc.leave_type=="Marriage - زواج" || frm.doc.leave_type=="Hajj leave - حج" ||frm.doc.leave_type=="Sick Leave - مرضية" || frm.doc.leave_type=="Educational - تعليمية" ){
        //         frm.fields_dict["attachment"].df.reqd=1;}
        //       else{
        //         frm.fields_dict["attachment"].df.reqd=0;}
        // }

    },

    // leave_approver: function(frm) {

    //     if (frm.doc.leave_approver) {
    //         frm.set_value("leave_approver_name", frappe.user.full_name(frm.doc.leave_approver));
    //     }
    // },

    employee: function(frm) {
        frm.trigger("get_leave_balance");
        // frm.trigger("calculate_monthly_accumulated_leave");
    },

    leave_type: function(frm) {
        frm.trigger("get_leave_balance");




    },

    half_day: function(frm) {
        if (frm.doc.from_date) {
            frm.set_value("to_date", frm.doc.from_date);
            frm.trigger("calculate_total_days");
        }
    },

    from_date: function(frm) {
        if (cint(frm.doc.half_day) == 1) {
            frm.set_value("to_date", frm.doc.from_date);
        }
        frm.trigger("calculate_total_days");
        if (frm.doc.to_date) {
            // frm.trigger("calculate_monthly_accumulated_leave");
        }
    },

    to_date: function(frm) {
        if (cint(frm.doc.half_day) == 1 && cstr(frm.doc.from_date) && frm.doc.from_date != frm.doc.to_date) {
            msgprint(__("To Date should be same as From Date for Half Day leave"));
            frm.set_value("to_date", frm.doc.from_date);
        }

        frm.trigger("calculate_total_days");
        // frm.trigger("calculate_monthly_accumulated_leave");
    },

    get_leave_balance: function(frm) {
        if (frm.doc.docstatus == 0 && frm.doc.employee && frm.doc.leave_type && frm.doc.from_date) {
            return frappe.call({
                method: "erpnext.hr.doctype.leave_application.leave_application.get_leave_balance_on",
                args: {
                    employee: frm.doc.employee,
                    date: frm.doc.from_date,
                    leave_type: frm.doc.leave_type,
                    consider_all_leaves_in_the_allocation_period: true
                },
                callback: function(r) {
                    if (!r.exc && r.message) {
                        frm.set_value('leave_balance', r.message);
                    }
                }
            });
        }
    },

    calculate_total_days: function(frm) {
        if (frm.doc.from_date && frm.doc.to_date) {
            if (cint(frm.doc.half_day) == 1) {
                frm.set_value("total_leave_days", 0.5);
            } else if (frm.doc.employee && frm.doc.leave_type) {
                // server call is done to include holidays in leave days calculations
                return frappe.call({
                    method: 'erpnext.hr.doctype.leave_application.leave_application.get_number_of_leave_days',
                    args: {
                        "employee": frm.doc.employee,
                        "leave_type": frm.doc.leave_type,
                        "from_date": frm.doc.from_date,
                        "to_date": frm.doc.to_date,
                        "half_day": frm.doc.half_day
                    },
                    callback: function(r) {
                        if (r && r.message) {
                            frm.set_value('total_leave_days', r.message);
                            frm.set_value('remaining_leave_days', parseFloat(frm.doc.leave_balance) - parseFloat(r.message));

                            frm.trigger("get_leave_balance");
                        }
                    }
                });
            }
        }
    },

    calculate_monthly_accumulated_leave: function(frm) {
        if (frm.doc.leave_type && frm.doc.employee && frm.doc.to_date && frm.doc.from_date) {
            if (frm.doc.leave_type == "Annual Leave - اجازة اعتيادية" || frm.doc.leave_type == "Compensatory off - تعويضية") {
                frappe.call({
                    method: "erpnext.hr.doctype.leave_application.leave_application.get_monthly_accumulated_leave",
                    args: {
                        "from_date": frm.doc.from_date,
                        "to_date": frm.doc.to_date,
                        "employee": frm.doc.employee,
                        "leave_type": frm.doc.leave_type
                    },
                    callback: function(r) {
                        if (frm.doc.docstatus != 1) {
                            // frm.set_value('monthly_accumulated_leave_balance', r.message);
                            // console.log(r);
                        }
                    }
                });
            } else {
                // frm.set_value('monthly_accumulated_leave_balance', '');
            }
        }
    }

});
