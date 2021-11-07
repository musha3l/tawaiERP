# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# from __future__ import unicode_literals
# import frappe
# from frappe.model.document import Document

# class BusinessTrip(Document):
#   pass


from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.data import getdate
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate
from datetime import date, datetime
from erpsystem import _send_email

class OverlapError(frappe.ValidationError): pass

class BusinessTrip(Document):
    def validate(self):
        # self.get_grade_info()
        self.validate_dates()
        # self.validate_leave_overlap()
        self.get_number_of_leave_days()
        self.get_ja_cost()
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
                if u'CEO' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By CEO"
                elif u'Director' in frappe.get_roles(employee_user) and self.days>4:
                    self.workflow_state = "Created By Director"
                elif u'Director' in frappe.get_roles(employee_user) and self.days<4:
                    self.workflow_state = "Create By Director"
                elif u'Manager' in frappe.get_roles(employee_user) and self.days>4:
                    self.workflow_state = "Created By Manager"
                elif u'Manager' in frappe.get_roles(employee_user) and self.days<4:
                    self.workflow_state = "Create By Manager"
                elif u'Line Manager' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By Line Manager"
                elif u'Employee' in frappe.get_roles(employee_user):
                    self.workflow_state = "Pending"

            if not employee_user and self.get('__islocal'):
                self.workflow_state = "Pending"


    def validate_dates(self):
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw(_('To Date field must be less than To Date field'))


    # def validate_leave_overlap(self):
    #   if not self.name:
    #       self.name = "New Job Assignment"
    #   for d in frappe.db.sql("""select *
    #       from `tabJob Assignment`
    #       where employee = %(employee)s and docstatus < 1
    #       and to_date >= %(from_date)s and from_date <= %(to_date)s
    #       and name != %(name)s""", {
    #           "employee": self.employee,
    #           "from_date": self.from_date,
    #           "to_date": self.to_date,
    #           "name": self.name
    #       }, as_dict = 1):
    #       self.throw_overlap_error(d)

    # def throw_overlap_error(self, d):
    #   msg = _("Employee {0} has already applied for {1} between {2} and {3}").format(self.employee,
    #       "Job Assignment", formatdate(d['from_date']), formatdate(d['to_date'])) \
    #       + """ <br><b><a href="#Form/Leave Application/{0}">{0}</a></b>""".format(d["name"])
    #   frappe.throw(msg, OverlapError)
        
    def before_insert(self):
        pass

    # def on_submit(self):
    #   # self.insert_expense_claim()
    #   # frappe.throw(frappe.session.user)
    #   if "Executive Manager" not in frappe.get_roles() and frappe.session.user != self.reports_to:
    #       frappe.throw(_("You are not permitted to submit"))
    #   # if (frappe.session.user != self.reports_to) or ()
    #   # self.notify()

    # def on_update_after_submit(self):
    #   self.notify()


    # def notify(self):
    #   owner = self.get_user(self.owner).email
    #   self.send_notify_mail(owner)

        # if self.workflow_state in [u'Approved By Direct Manager', u'Rejected']:
        #   department_managers = [i['email'] for i in self.get_department_managers()]
        #   self.send_notify_mail(department_managers)
        #
        # if self.workflow_state in [u'Approved By Direct Manager']:
        #   users = [i['email'] for i in self.get_users_in_role(u'Accounts User')]
        #   self.send_notify_mail(users)

    # def send_notify_mail(self,recipients):
    #   # recipients = ['oashour9@gmail.com' for i in recipients]
    #   subject = _(self.doctype)
    #   data = {'doctype':_(self.doctype), 'name':self.name, 'state':'--'}

    #   _send_email(data, recipients, subject, 'docstate_update.html')

    def get_department_managers(self):
        department = self.get_department()
        query = """select user.* from tabEmployee employee
                            Inner Join tabUserRole role on employee.user_id = role.parent
                            Inner Join tabUser user on employee.user_id = user.name
                            where role.role = 'Department Manager' and employee.department='{department}'"""

        department_managers = frappe.db.sql(query.format(department=frappe.db.escape(department)), as_dict=1)
        return department_managers

    def get_department(self):
        employee = frappe.get_doc('Employee', {'user_id': self.owner})
        department = employee.department
        return department

    def get_users_in_role(self, role_name):
        query = """select user.* from tabUser user
                                    Inner Join tabUserRole role on user.name = role.parent
                                    where role.role = '{role}'"""
        users = frappe.db.sql(query.format(role=frappe.db.escape(role_name)), as_dict=1)
        return users

    def get_user(self, user):
        return frappe.get_doc('User', {'name': user})

    def get_employee(self, user):
        return frappe.get_doc('Employee', {'user_id': user})

    # def insert_expense_claim(self):
    #   fields = {
    #   _('Total'):self.total,
    #   }
    #   if self.assignment_type=="In City Assign" :
    #       fields[_('Transportation Costs')]=self.transportation_costs
    #   expenses=[]# other_costs training_cost accommodation_cost living_costs transportation_costs
    #   for key,value in fields.iteritems():
    #       if value >0:
    #           expense_claim_details = frappe.new_doc("Expense Claim Detail")
    #           expense_claim_details.update( {
    #           "claim_amount": value,
    #           "sanctioned_amount":  value,
    #           "description":key,
    #           "parentfield": "expenses"
    #           })
    #           expenses.append( expense_claim_details )

    #   expense_claim = frappe.get_doc({
    #   "doctype": "Expense Claim",
    #   "naming_series": "EXP",
    #   "exp_approver": self.get_department_managers()[0].name,
    #   "employee": self.employee,
    #   "expenses":expenses,
    #   "reference_type":"Job Assignment",
    #   "reference_name":self.name,
    #   "remark":self.assignment_type
    #   })
    #   # print '='*50
    #   # print expenses
    #   # print '=' * 50
    #   expense_claim.save()

    

    # def get_days_of_jobAssingment(self):
    #   list =frappe.db.sql("""select sum(diff) as total from(select datediff(to_date, from_date)
    #    as diff from `tabJob Assignment` where employee = %(employee)s and docstatus =1 and YEAR(from_date) = YEAR(%(from_date)s)) as result;
    #       """, {
    #           "employee": self.employee,
    #           "from_date": self.from_date,
    #       }, as_dict = 1)
    #   if list:
    #       return list[0]['total']
    #   else:
    #       return -1

    def get_employee_from_session (self):
        if self.get('__islocal'):
            employee = frappe.get_list("Employee", fields=["name","employee_name","grade"]
            , filters = {"user_id":frappe.session.user},ignore_permissions=True)
            if employee != []:
                self.employee = employee[0].name
                self.employee_name = employee[0].employee_name



    def get_number_of_leave_days(self):
        if self.to_date and self.from_date:
            number_of_days = date_diff(self.to_date, self.from_date)
            if number_of_days<0:
                self.days = 0
                return 0
            self.days=number_of_days+1
            # return number_of_days+1

    def get_grade_info(self):
        emp = frappe.get_doc("Employee",self.employee)
        grade = frappe.get_doc("Grade",emp.grade)
        frappe.throw(emp.grade)
        # self.internal_per_diem_rate = grade.internal_per_diem_rate
        # self.external_per_diem_rate = grade.external_per_diem_rate
        # self.internal_ticket_class = grade.internal_ticket_class
        # self.external_ticket_class = grade.external_ticket_class

    def get_ja_cost(self):
        total =0.0
        emp = frappe.get_doc("Employee",self.employee)
        grade_doc = frappe.get_doc("Grade",emp.grade)
        if self.days:
            if self.assignment_type=="Internal":
                total = flt(self.days)*flt(self.internal_per_diem_rate) +self.ticket_cost
            if self.assignment_type=="External":
                total = flt(self.days)*flt(self.external_per_diem_rate)+self.ticket_cost
                
        self.cost_total = total
        self.get_total_cost()

    def get_total_cost(self):
        total =0.0
        if self.assignment_type=="In City Assign" :
            total = flt(self.transportation_costs)*flt(self.days)
        if self.assignment_type=="Internal" or self.assignment_type=="External":
            total = flt(self.cost_total)
        self.total = total


    def get_default_cost_center(self,company):
        cost_center = frappe.get_doc('Company', company)
        return cost_center.cost_center


    def get_current_user(self):
        user = frappe.session.user
        employees = frappe.get_list("Employee", fields=["name"], filters={'user_id': user}, ignore_permissions=True)
        if employees:
            employee = frappe.get_doc('Employee', {'name': employees[0].name})
            return employee

