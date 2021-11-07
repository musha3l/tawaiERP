# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ExitReEntryApplication(Document):
    def validate(self):
        if self.exit_type== "VISA":
            if not self.country:
                frappe.throw("Kindly choose country when select 'VISA'") 

        self.validate_emp()
        if self.workflow_state:
            if "Rejected" in self.workflow_state:
                self.docstatus = 1
                self.docstatus = 2

    def validate_emp(self):
        if self.employee:
            employee_user = frappe.get_value("Employee", filters={"name": self.employee}, fieldname="user_id")
            if self.get('__islocal') and employee_user:
                if u'CEO' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By CEO"
                elif u'Director' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By Director"
                elif u'Manager' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By Manager"
                elif u'Line Manager' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By Line Manager"
                elif u'Employee' in frappe.get_roles(employee_user):
                    self.workflow_state = "Pending"

            if not employee_user and self.get('__islocal'):
                self.workflow_state = "Pending"


    # def on_submit(self):
    #   leave=frappe.get_doc("Leave Application",self.application_requested)
    #   mng=frappe.db.sql("select name from tabEmployee where user_id in(select name from tabUser where name in(select parent from tabUserRole where role='Ticket Approver'))")
    #   if mng:
    #       manag=frappe.get_doc("Employee",mng[0][0])

    #   if self.docstatus==1 and leave.ticket==1:
    #       family_info= leave.get("ticket_family_members")
    #       ticreq= frappe.get_doc({
    #           "doctype":"Ticket Request",
    #           "employee": leave.employee,
    #           "application_type": "Leave Application",
    #           "application_requested": leave.name
    #           }).insert(ignore_permissions=True)
    #       if family_info:
    #           ticreq.set("family_members",family_info)
    #           ticreq.save()


    #       frappe.db.sql("update `tabLeave Application` set workflow_state='Approved By GR Supervisor',next_stage='Approved By Ticket Approver',approval_manager='{0}' where name='{1}'".format(manag.employee_name,self.application_requested))
        
    #   elif self.docstatus==1:
    #       frappe.db.sql("update `tabLeave Application` set workflow_state='Approved By GR Supervisor',next_stage='--',approval_manager='--' where name='{0}'".format(self.application_requested))

