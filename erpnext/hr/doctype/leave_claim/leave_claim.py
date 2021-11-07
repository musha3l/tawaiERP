# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

class LeaveClaim(Document):
    def validate(self):
        self.validate_emp()

        if hasattr(self,"workflow_state"):
            if self.workflow_state:
                if "Rejected" in self.workflow_state:
                    self.docstatus = 1
                    self.docstatus = 2

    def validate_emp(self):
        if self.employee:
            employee_user = frappe.get_value("Employee", filters={"name": self.employee}, fieldname="user_id")
            if self.get('__islocal') and employee_user:
                if u'Director' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By Director"
                elif u'Manager' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By Manager"
                elif u'Line Manager' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By Line Manager"
                elif u'Employee' in frappe.get_roles(employee_user):
                    self.workflow_state = "Pending"

            if not employee_user and self.get('__islocal'):
                self.workflow_state = "Pending"

    def on_submit(self):
        leave_from_date = datetime.datetime.strptime(str(self.from_date), '%Y-%m-%d')
        updated_leave_date = date(leave_from_date.year, leave_from_date.month, leave_from_date.day) + relativedelta(days=+len(self.leave_claim_days))

        if self.leave_application:
            doc = frappe.get_doc("Leave Application", self.leave_application)
            doc.total_leave_days = doc.total_leave_days-len(self.leave_claim_days)
            doc.from_date = str(updated_leave_date)
            doc.save(ignore_permissions=True)

    def validate_claim_date(self):
        frappe.msgprint("Claim Date must be between {0} and {1}".format(self.from_date,self.to_date))

    def validate_exist_date(self,date):
        frappe.msgprint("Date {0} is already entered".format(date))
