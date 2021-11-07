# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, date_diff, formatdate
from frappe import _
from frappe.model.document import Document
from erpnext.hr.utils import set_employee_name
from erpnext.hr.doctype.leave_application.leave_application import get_approved_leaves_for_period

class OverlapError(frappe.ValidationError): pass
class BackDatedAllocationError(frappe.ValidationError): pass
class OverAllocationError(frappe.ValidationError): pass
class LessAllocationError(frappe.ValidationError): pass
class ValueMultiplierError(frappe.ValidationError): pass

class LeaveAllocation(Document):
    def validate(self):
        self.validate_period()
        # self.validate_new_leaves_allocated_value()
        self.validate_allocation_overlap()
        self.validate_back_dated_allocation()
        self.set_total_leaves_allocated()
        self.validate_total_leaves_allocated()
        self.validate_lwp()
        set_employee_name(self)

    def on_update_after_submit(self):
        # self.validate_new_leaves_allocated_value()
        self.set_total_leaves_allocated()

        frappe.db.set(self,'carry_forwarded_leaves', flt(self.carry_forwarded_leaves))
        frappe.db.set(self,'total_leaves_allocated',flt(self.total_leaves_allocated))

        self.validate_against_leave_applications()

    def validate_period(self):
        if date_diff(self.to_date, self.from_date) <= 0:
            frappe.throw(_("To date cannot be before from date"))

    def validate_lwp(self):
        if frappe.db.get_value("Leave Type", self.leave_type, "is_lwp"):
            frappe.throw(_("Leave Type {0} cannot be allocated since it is leave without pay").format(self.leave_type))

    def validate_new_leaves_allocated_value(self):
        """validate that leave allocation is in multiples of 0.5"""
        if flt(self.new_leaves_allocated) % 0.5:
            frappe.throw(_("Leaves must be allocated in multiples of 0.5"), ValueMultiplierError)

    def validate_allocation_overlap(self):
        leave_allocation = frappe.db.sql("""
            select name from `tabLeave Allocation`
            where employee=%s and leave_type=%s and docstatus=1
            and to_date >= %s and from_date <= %s""",
            (self.employee, self.leave_type, self.from_date, self.to_date))

        if leave_allocation:
            frappe.msgprint(_("{0} already allocated for Employee {1} for period {2} to {3}")
                .format(self.leave_type, self.employee, formatdate(self.from_date), formatdate(self.to_date)))

            frappe.throw(_('Reference') + ': <a href="#Form/Leave Allocation/{0}">{0}</a>'
                .format(leave_allocation[0][0]), OverlapError)

    def validate_back_dated_allocation(self):
        future_allocation = frappe.db.sql("""select name, from_date from `tabLeave Allocation`
            where employee=%s and leave_type=%s and docstatus=1 and from_date > %s
            and carry_forward=1""", (self.employee, self.leave_type, self.to_date), as_dict=1)

        if future_allocation:
            frappe.throw(_("Leave cannot be allocated before {0}, as leave balance has already been carry-forwarded in the future leave allocation record {1}")
                .format(formatdate(future_allocation[0].from_date), future_allocation[0].name),
                    BackDatedAllocationError)

    def set_total_leaves_allocated(self):
        self.carry_forwarded_leaves = get_carry_forwarded_leaves(self.employee,
            self.leave_type, self.from_date, self.carry_forward)

        self.total_leaves_allocated = flt(self.carry_forwarded_leaves) + flt(self.new_leaves_allocated)

        if not self.total_leaves_allocated:
            frappe.throw(_("Total leaves allocated is mandatory"))

    def validate_total_leaves_allocated(self):
        # Adding a day to include To Date in the difference
        date_difference = date_diff(self.to_date, self.from_date) + 1
        if date_difference < self.total_leaves_allocated:
            frappe.throw(_("Total allocated leaves are more than days in the period"), OverAllocationError)

    def validate_against_leave_applications(self):
        leaves_taken = get_approved_leaves_for_period(self.employee, self.leave_type,
            self.from_date, self.to_date)

        if flt(leaves_taken) > flt(self.total_leaves_allocated):
            if frappe.db.get_value("Leave Type", self.leave_type, "allow_negative"):
                frappe.msgprint(_("Note: Total allocated leaves {0} shouldn't be less than already approved leaves {1} for the period").format(self.total_leaves_allocated, leaves_taken))
            else:
                frappe.throw(_("Total allocated leaves {0} cannot be less than already approved leaves {1} for the period").format(self.total_leaves_allocated, leaves_taken), LessAllocationError)

@frappe.whitelist()
def get_carry_forwarded_leaves(employee, leave_type, date, carry_forward=None):
    carry_forwarded_leaves = 0

    if carry_forward:
        validate_carry_forward(leave_type)

        previous_allocation = frappe.db.sql("""
            select name, from_date, to_date, total_leaves_allocated
            from `tabLeave Allocation`
            where employee=%s and leave_type=%s and docstatus=1 and to_date < %s
            order by to_date desc limit 1
        """, (employee, leave_type, date), as_dict=1)
        if previous_allocation:
            leaves_taken = get_approved_leaves_for_period(employee, leave_type,
                previous_allocation[0].from_date, previous_allocation[0].to_date)

            carry_forwarded_leaves = flt(previous_allocation[0].total_leaves_allocated) - flt(leaves_taken)

    return carry_forwarded_leaves

def validate_carry_forward(leave_type):
    if not frappe.db.get_value("Leave Type", leave_type, "is_carry_forward"):
        frappe.throw(_("Leave Type {0} cannot be carry-forwarded").format(leave_type))

def get_users_exceed_max_leave_allocation():
    notify_emps = []
    allocation = frappe.db.sql("""  select employee,max(from_date),max(to_date),total_leaves_allocated from `tabLeave Allocation` where leave_type='Annual Leave - اجازة اعتيادية' group by employee  """)
    for i in range(len(allocation)):
        # print allocation[i][0],allocation[i][1],allocation[i][2]

        leave = frappe.db.sql(""" select employee,creation,total_leave_days from `tabLeave Application` where leave_type='Annual Leave - اجازة اعتيادية' and docstatus=1 and employee='{0}' and creation between '{1}' and '{2}' """.format(allocation[i][0],allocation[i][1],allocation[i][2]))
        # print leave

        if allocation[i][3] >= 30:
            notify_emps.append(allocation[i][0].encode('ascii'))
            print notify_emps
            for l in range(len(leave)):
                if leave[l][0] == allocation[i][0]:
                    print allocation[i][3] - leave[l][2]
                    if allocation[i][3] - leave[l][2] < 30:
                        del notify_emps[-1]

    usr = ()
    if notify_emps:
        if len(notify_emps) == 1:
            usr = frappe.db.sql(""" select user_id from `tabEmployee` where employee = '{0}' """.format(notify_emps[0]))
        else:
            usr = frappe.db.sql(""" select user_id from `tabEmployee` where employee in {0} """.format((tuple(notify_emps))))

    return usr

def check_max_allocation_balance():
    from frappe.core.doctype.communication.email import make
    frappe.flags.sent_mail = None
    content_msg="Your Annual Leave balance exceeded 30 days, Please use them !"


    allocated_balance = get_users_exceed_max_leave_allocation()
    if allocated_balance:
        for i in allocated_balance:
            prefered_email = frappe.get_value("Employee", filters = {"user_id": i[0]}, fieldname = "prefered_email")
            print prefered_email
            if prefered_email:

                try:
                    print prefered_email
                    # make(subject = "Max Annual Leave exceeded", content=content_msg, recipients=prefered_email,
                    #     send_email=True, sender="erp@tawari.sa")
                except:
                    frappe.msgprint("could not send")

# def check_max_allocation_balance():
#     from frappe.core.doctype.communication.email import make
#     frappe.flags.sent_mail = None
#     content_msg="Your Annual Leave balance exceeded 30 days, Please use them !"

#     allocated_balance = frappe.db.sql("select user_id from `tabEmployee` where name in (select employee from `tabLeave Allocation` where leave_type ='Annual Leave - اجازة اعتيادية' and total_leaves_allocated >=30 )")
#     for i in allocated_balance:
#         prefered_email = frappe.get_value("Employee", filters = {"user_id": i[0]}, fieldname = "prefered_email")

#         if prefered_email:

#             try:
#                 make(subject = "Max Annual Leave exceeded", content=content_msg, recipients=prefered_email,
#                     send_email=True, sender="erp@tawari.sa")
#             except:
#                 frappe.msgprint("could not send")


@frappe.whitelist(allow_guest=True)
def get_annual_and_emergency_balanch(employee):
    emp = frappe.db.sql("select name from `tabEmployee` where user_id ='{0}'".format(employee))


    remain_annual = frappe.db.sql(""" select (select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'Annual Leave - اجازة اعتيادية' and docstatus =1 order by creation desc limit 1 ) - ( select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='Annual Leave - اجازة اعتيادية' and docstatus=1  )""".format(emp[0][0]))
    max_annual = frappe.db.sql(""" select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'Annual Leave - اجازة اعتيادية' and docstatus =1 order by creation desc limit 1 """.format(emp[0][0]))
    used_annual = frappe.db.sql(""" select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='Annual Leave - اجازة اعتيادية' and docstatus=1 """.format(emp[0][0]))

    remain_emergency = frappe.db.sql(""" select (select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'emergency -اضطرارية' and docstatus =1 order by creation desc limit 1 ) - ( select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='emergency -اضطرارية' and docstatus=1  )""".format(emp[0][0]))
    max_emergency = frappe.db.sql(""" select total_leaves_allocated from `tabLeave Allocation` where employee='{0}' and leave_type = 'emergency -اضطرارية' and docstatus =1 order by creation desc limit 1 """.format(emp[0][0]))
    used_emergency = frappe.db.sql(""" select SUM(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='emergency -اضطرارية' and docstatus=1 """.format(emp[0][0]))

    if used_annual[0][0]:
        remain_annual = remain_annual
    else:
        remain_annual = max_annual

    if used_emergency[0][0]:
        remain_emergency = remain_emergency
    else:
        remain_emergency = max_emergency

    return remain_annual[0][0],remain_emergency[0][0]
