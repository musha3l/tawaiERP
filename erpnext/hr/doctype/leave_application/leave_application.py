# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import math
from frappe import _
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, \
    comma_or, get_fullname, add_years, add_months, add_days, nowdate
from erpnext.hr.utils import set_employee_name
from erpnext.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.hr.doctype.employee_leave_approver.employee_leave_approver import get_approver_list
from erpnext.setup.doctype.sms_settings.sms_settings import send_sms
import datetime



class LeaveDayBlockedError(frappe.ValidationError): pass
class OverlapError(frappe.ValidationError): pass
class InvalidLeaveApproverError(frappe.ValidationError): pass
class LeaveApproverIdentityError(frappe.ValidationError): pass
class AttendanceAlreadyMarkedError(frappe.ValidationError): pass

from frappe.model.document import Document
class LeaveApplication(Document):
    pass
    def get_feed(self):
        return _("{0}: From {0} of type {1}").format(self.status, self.employee_name, self.leave_type)

    def validate(self):
        frappe.clear_cache(user=frappe.session.user)
        user_roles = frappe.get_roles()
        if not getattr(self, "__islocal", None) and frappe.db.exists(self.doctype, self.name):
            self.previous_doc = frappe.db.get_value(self.doctype, self.name, "*", as_dict=True)
        else:
            self.previous_doc = None

        set_employee_name(self)
        #~ # self.validate_death_and_newborn_leave()
        self.validate_emp()
        self.validate_yearly_repeated_leaves()
        self.validate_dates()
        self.validate_balance_leaves()
        self.validate_leave_overlap()
        self.validate_max_days()
        self.show_block_day_warning()
        self.validate_block_days()
        self.validate_salary_processed_days()
        # if not "HR Manager" in user_roles:
        #   self.validate_leave_approver()
        self.validate_attendance()
        self.validate_back_days()
        self.validate_monthly_leave()
        # self.validate_approval_line_manager()
        # self.validate_type()
        # self.validate_days_and_fin()
        # self.set_approvals()
        self.validate_leave_submission_dates()
        self.validate_conditional_workflow_transition()
        self.get_department()
        self.validate_three_month_joining()

        #~ # self.update_leaves_allocated()
        #~ result=frappe.db.sql("select name from tabCommunication where reference_name='{0}' and subject='Approved By Line Manager'".format(self.name))


    def validate_leave_submission_dates(self):
        if u'HR User' not in frappe.get_roles(frappe.session.user) and self.get('__islocal'):
            if self.leave_type == "Annual Leave - اجازة اعتيادية":
                if date_diff(nowdate(), self.from_date) > 3:
                    frappe.throw(_("Cannot apply for annual leave in same day"))
            if self.leave_type == "emergency -اضطرارية":
                if date_diff(nowdate(), self.from_date) > 3:
                    frappe.throw(_("The submission date must be less than or equal 3 days after leave start"))
            if self.leave_type == "Marriage - زواج" or self.leave_type == "New Born - مولود جديد" or self.leave_type == "Death - وفاة":
                if date_diff(nowdate(), self.to_date) > 15:
                    frappe.throw(_("The submission date must not exceed 15 days after leave end"))
            if self.leave_type == "Hajj leave - حج":
                if date_diff(self.from_date, nowdate()) < 10:
                    frappe.throw(_("The submission date must before 10 days from leave start"))
            if self.leave_type == "Sick Leave - مرضية":
                if date_diff(nowdate(), self.to_date) > 10:
                    frappe.throw(_("The submission date must not exceed 10 days after leave end"))
            if self.leave_type == "Educational - تعليمية":
                if date_diff(self.from_date, nowdate()) < 15:
                    frappe.throw(_("The submission date must be greater than or equal 15 days before leave start"))
            if self.leave_type == "Without Pay - غير مدفوعة":
                if date_diff( nowdate(), self.from_date) >= 0:
                    frappe.throw(_("The submission date can't be after leave start"))

    # def set_approvals(self):
    #   user = frappe.session.user
    #   employee = frappe.get_list("Employee", fields=["name"], filters={'user_id': user}, ignore_permissions=True)
    #   if employee:
    #       emp=frappe.get_doc("Employee",employee[0].name)
    #       # frappe.msgprint(employee[0].name)
    #       app=self.get("approvals")
    #       if (not self.get('__islocal')) and (self.workflow_state=="Pending" or self.workflow_state=="Created By Manager" or self.workflow_state=="Created By Director"):
    #           pass
    #       else:
    #           app.append({
    #               "approval" :employee[0].name,
    #               "approval_name":emp.employee_name,
    #               "state":self.workflow_state,
    #               "date" :frappe.utils.data.now_datetime()
    #               })
    #           self.set("approvals",app)

    def validate_emp(self):
        if self.employee:
            employee_user = frappe.get_value("Employee", filters = {"name": self.employee}, fieldname="user_id")
            if self.get('__islocal') and employee_user:
                if u'CEO' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By CEO"
                elif u'Director' in frappe.get_roles(employee_user):
                    self.workflow_state = "Created By Director"
                elif u'Manager' in frappe.get_roles(employee_user):
                        self.workflow_state = "Created By Manager"
                elif u'Line Manager' in frappe.get_roles(employee_user):
                        self.workflow_state = "Created By Line Manager"
                else:
                    self.workflow_state = "Pending"

            if not employee_user and self.get('__islocal'):
                self.workflow_state = "Pending"


    def after_insert(self):
        # self.get_department()
        # frappe.clear_cache(user=frappe.session.user)

        # if self.workflow_state=="Approved By Manager":
        #   #frappe.db.sql("update tabCommunication set subject ='Approved By Manager' , content='Approved By Manager' where reference_name ='{0}' and subject ='Approved By Line Manager'".format(self.name))
        #   # frappe.msgprint("111")
        #   pass
        if self.leave_type != "Annual Leave - اجازة اعتيادية" and self.leave_type != "Without Pay - غير مدفوعة" and self.leave_type != "Compensatory off - تعويضية" and self.leave_type != "emergency -اضطرارية":
            frappe.msgprint(_("You must attach the required file otherwise the application will be <span style='color:red;'>REJECTED!</span>"))

    def get_department(self):
        dep = frappe.get_value("Employee", filters = {"name": self.employee}, fieldname = "department")
        if not dep:
            frappe.throw(_("The department should be set to this employee in the Employee form"))
        else:
            self.department = dep


    def validate_three_month_joining(self):
        if self.leave_type == 'Annual Leave - اجازة اعتيادية':
            if getdate(nowdate()) < getdate(add_months(self.date_of_joining,3)):
                frappe.throw("You cant apply for leave application of type Annual Leave - اجازة اعتيادية before {0}".format(getdate(add_months(self.date_of_joining,3))))


    def validate_conditional_workflow_transition(self):

        def unpaid_leave_switcher():
            if self.leave_type == "Without Pay - غير مدفوعة" and self.workflow_state == "Approved By Director":
                    applied_days = has_approved_leave(self.leave_type, self.employee)
                    if applied_days or self.total_leave_days > 10:
                        self.workflow_state = "Approved By Director (U.L)"
        def workflow_leave_switcher(wf = self.workflow_state, ld = self.total_leave_days, lt = self.leave_type):
             # New Code For higher than 30 days, ceo check
            if ld >= 30:
                if lt == 'Annual Leave - اجازة اعتيادية':
                    if wf == "Approved By HR Specialist":
                        self.workflow_state = "Approved By HR Specialist (+30)"
                    elif wf == "Approved By HR Manager":
                        self.workflow_state = "Approved By HR Manager (+30)"

            elif ld > 5:
                if wf == "Approved By Director" and (lt == " Annual Leave - اجازة اعتيادية" or lt == " emergency -اضطرارية" or lt == " Without Pay - غير مدفوعة"):
                    self.workflow_state = "Approved By Director (+5)"

                elif wf == "Approved By CEO":
                    self.workflow_state = "Approved By CEO (+5 U.L)"


            else:
                if wf == "Approved By HR Specialist":
                    self.workflow_state = "Approved By HR Specialist (F.T)"
                    self.flags.ignore_permissions = True
                    self.status = "Approved"
                    self.docstatus = 1
            if wf == "Approved By Director" and lt == "Compensatory off - تعويضية":
                self.workflow_state = "Approved By Director (F.T)"
                self.flags.ignore_permissions = True
                self.status = "Approved"
                self.docstatus = 1
            elif wf == "Approved By HR Manager" :
                self.flags.ignore_permissions = True
                self.status = "Approved"
        def created_by_ceo():
            if self.workflow_state == "Created By CEO":
                self.status = "Approved"
                self.docstatus = 1

        unpaid_leave_switcher()
        workflow_leave_switcher()
        created_by_ceo()

    def unallowed_actions(self):
        if hasattr(self,"workflow_state"):
            permitted_departments = frappe.db.sql_list("select for_value from `tabUser Permission` where allow = 'Department' and user = '{0}'".format(frappe.session.user))
            if self.department not in permitted_departments and 'HR Manager' in frappe.get_roles(frappe.session.user) and self.workflow_state in ["Created By Manager", "Approved by Manager"]:
                return True
            elif self.department not in permitted_departments and 'HR Specialist' in frappe.get_roles(frappe.session.user) and self.workflow_state in ["Pending", "Created By Line Manager", "Approved By Line Manager"]:
                return True
    # def validate_approval_line_manager(self):
    #   dd=frappe.get_doc("Employee",self.employee)
    #   if dd.sub_department:
    #       dep=frappe.get_doc("Department",dd.sub_department)
    #       if dep.is_group==0 and (not dep.line_manager):
    #           user_roles = frappe.get_roles()
    #           if  "Manager" in user_roles:
    #               if  dep.manager and self.workflow_state=="Approved By Line Manager":
    #                   self.workflow_state="Approved By Manager"
    #               if  dep.manager and self.workflow_state=="Rejected By Line Manager":
    #                   self.workflow_state="Rejected By Manager"
    #                   # result=frappe.db.sql("select name from tabCommunication where reference_name='{0}' and subject='Approved By Line Manager'".format(self.name))

    #      #                if result:
    #                   #     frappe.msgprint(result[0][0])

    # def validate_type(self):

    #   le_list=frappe.get_list("Leave Application",['name'],filters={"leave_type":"Without Pay - غير مدفوعة","employee":self.employee,"status":"Approved"})
    #   user_roles = frappe.get_roles()


    #   if  "HR Specialist" in user_roles:
    #       if not ((le_list and self.leave_type=="Without Pay - غير مدفوعة") or (self.leave_type=="Without Pay - غير مدفوعة" and self.total_leave_days >10)):
    #           if self.workflow_state=="Approved By CEO":
    #               frappe.db.sql("update `tabLeave Application` set workflow_state='Approved By HR Specialist' where name ='{0}'".format(self.employee))
    #               self.workflow_state="Approved By HR Specialist"

    #           if self.workflow_state=="Rejected By CEO":
    #               self.workflow_state="Rejected By HR Specialist"


    #   if "HR Manager" in user_roles:
    #       if (self.leave_type=="Without Pay - غير مدفوعة" or self.leave_type=="Annual Leave - اجازة اعتيادية" or self.leave_type=="emergency -اضطرارية") and self.total_leave_days>5:
    #           if self.workflow_state=="Approved By HR Specialist":
    #               self.workflow_state="Approved By HR Manager"

    #           if self.workflow_state=="Approved By CEO":
    #               self.workflow_state="Approved By HR Manager"

    #           if self.workflow_state=="Rejected By HR Specialist":
    #               self.workflow_state="Rejected By HR Manager"

    #           if self.workflow_state=="Rejected By CEO":
    #               self.workflow_state="Rejected By HR Manager"




    # def validate_days_and_fin(self):
    #   if not((self.total_leave_days <5 and self.leave_type=="Without Pay - غير مدفوعة") or self.total_leave_days >5):
    #       if self.workflow_state=="Approved By HR Specialist":
    #           self.status="Approved"
    #           self.docstatus=1
    #           ''' start form here by ahmad  to allow ceo to add leave application directally
    #           without the need for hr manager to approve it which make it status = approved and 1
    #           , yet the hr manager can approve it and it would be
    #           just deccoratoed '''
    #   #commented nisma two lines
    #   #else:
    #       # if self.workflow_state=="Approved By HR Manager":
    #       elif self.workflow_state=="Approved By HR Manager":
    #           self.status="Approved"
    #           self.docstatus=1
    #   #added by ahmad
    #       elif self.workflow_state=="Created By CEO":
    #           self.status="Approved"
    #           self.docstatus=1

    #           ''' end to here by ahmad '''


    #   if "Rejected" in str(self.workflow_state):
    #       self.status="Rejected"
    #       self.docstatus=2



    # def validate_type_dis(self):

    #   user = frappe.session.user
    #   employee = frappe.get_list("Employee", fields=["name"], filters={'user_id': user}, ignore_permissions=True)
    #   if employee:

    #       # department = frappe.get_value("Department" , filters= {"manager": employee[0].name}, fieldname="name")
    #       emplo=frappe.get_doc("Employee",self.employee)
    #       if emplo.sub_department:
    #           department_doc=frappe.get_doc("Department",emplo.sub_department)
    #       if emplo.department:
    #           department_doc_main=frappe.get_doc("Department",emplo.department)
    #       if emplo.user_id:
    #           userem=frappe.get_doc("User",emplo.user_id)

    #   #result=frappe.db.sql("select name from tabCommunication where reference_name='{0}' and subject='Approved By Line Manager'".format(self.name))
    #   # if result:
    #   #     frappe.msgprint(result[0][0])
    #   fl=False
    #   le_list=frappe.get_all("Leave Application",['name'],filters={"leave_type":"Without Pay - غير مدفوعة","employee":self.employee,"workflow_state":"Approved By HR Manager"})
    #   user_roles = frappe.get_roles()

    #   if not self.get('__islocal'):
    #       if (not("Manager" in user_roles)) and self.workflow_state=="Pending":
    #           # frappe.msgprint(("Manager" in user_roles))
    #           fl=True

    #       if self.workflow_state:
    #           if 'Rejected' in self.workflow_state :
    #               fl=True
    #       if  ("CEO" in user_roles and frappe.session.user != "Administrator") :
    #           if not self.workflow_state=="Created By Director":
    #               if not ((le_list and self.leave_type=="Without Pay - غير مدفوعة") or (self.leave_type=="Without Pay - غير مدفوعة" and self.total_leave_days >10)):
    #                   fl= True
    #       if "HR Manager" in user_roles and frappe.session.user != "Administrator" :
    #           if self.workflow_state=="Approved by Manager" or  self.workflow_state=="Created By Manager":
    #               if department_doc_main.director !=  employee[0].name:

    #                   fl=True
    #               else:
    #                   return


    #           elif not (((((self.leave_type=="Wihout Pay - غير مدفوعة" and self.total_leave_days<=10) or self.leave_type=="Annual Leave - اجازة اعتيادية" or self.leave_type=="emergency -اضطرارية") and self.total_leave_days>5 )and self.workflow_state=="Approved By Director" )or (((le_list and self.leave_type=="Without Pay - غير مدفوعة") or (self.leave_type=="Without Pay - غير مدفوعة" and self.total_leave_days >10)) and self.workflow_state=="Approved By CEO" ) or (self.leave_type=="Without Pay - غير مدفوعة"  and self.workflow_state=="Approved By HR Specialist" ) or self.workflow_state=="Created By CEO" or (u"Director" in frappe.get_roles(userem.name) and self.workflow_state=="Approved By CEO" and self.total_leave_days>5 and (self.leave_type=="Wihout Pay - غير مدفوعة"  or self.leave_type=="Annual Leave - اجازة اعتيادية" or self.leave_type=="emergency -اضطرارية"))):
    #               if ( self.total_leave_days>5 )and self.workflow_state=="Approved By Director":
    #                   if (self.leave_type=="Without Pay - غير مدفوعة" and self.total_leave_days<=10)or self.leave_type=="Annual Leave - اجازة اعتيادية" or self.leave_type=="emergency -اضطرارية":
    #                       return
    #               if (not(self.leave_type=="Wihout Pay - غير مدفوعة"  or self.leave_type=="Annual Leave - اجازة اعتيادية" or self.leave_type=="emergency -اضطرارية")) and self.total_leave_days>5 and self.workflow_state=="Approved By HR Specialist":
    #                   return



    #               fl=True


    #           elif self.total_leave_days <5 and self.workflow_state=="Approved By HR Specialist" and self.leave_type!="Without Pay - غير مدفوعة":
    #               fl=True

    #           elif (self.total_leave_days <5 and self.workflow_state=="Approved By Director"):
    #               fl=True





    #       if "HR Specialist" in user_roles and frappe.session.user != "Administrator" :
    #           if ((self.workflow_state=="Approved By CEO" or (((self.leave_type=="Without Pay - غير مدفوعة" and self.total_leave_days<10)or self.leave_type=="Annual Leave - اجازة اعتيادية" or self.leave_type=="emergency -اضطرارية" ) and self.workflow_state=="Approved By Director")) and self.total_leave_days>5):
    #               fl= True
    #           # if self.total_leave_days>5:
    #           #   if not(self.workflow_state=="Pending" and department_doc.manager ==  employee[0].name):
    #           #       fl=True
    #           if (not((self.leave_type=="Without Pay - غير مدفوعة" and self.total_leave_days<10)or self.leave_type=="Annual Leave - اجازة اعتيادية" or self.leave_type=="emergency -اضطرارية" )) and self.workflow_state=="Approved By Director" and self.total_leave_days>5:
    #               return

    #           if (((le_list and self.leave_type=="Without Pay - غير مدفوعة") or (self.leave_type=="Without Pay - غير مدفوعة" and self.total_leave_days >10))and self.workflow_state=="Approved By Director") :
    #               fl=True

    #           elif self.workflow_state=="Pending"  :
    #               if department_doc.manager !=  employee[0].name:
    #                   fl=True

    #           elif self.workflow_state=="Created By CEO":
    #               fl=True

    #           elif self.workflow_state=="Approved By Director" and (not((le_list and self.leave_type=="Without Pay - غير مدفوعة") or (self.leave_type=="Without Pay - غير مدفوعة" and self.total_leave_days >10))) and self.total_leave_days <5:
    #               return



    #           elif u"Director" in frappe.get_roles(userem.name) and self.workflow_state=="Approved By CEO" and (not(self.total_leave_days>5 and (self.leave_type=="Wihout Pay - غير مدفوعة"  or self.leave_type=="Annual Leave - اجازة اعتيادية" or self.leave_type=="emergency -اضطرارية"))):
    #               return
    #           elif u"Director" in frappe.get_roles(userem.name) and self.workflow_state=="Approved By CEO" :
    #               if self.total_leave_days>5 and (self.leave_type=="Wihout Pay - غير مدفوعة"  or self.leave_type=="Annual Leave - اجازة اعتيادية" or self.leave_type=="emergency -اضطرارية"):
    #                   fl=True


    #           elif not (self.workflow_state=="Approved By CEO" and ((le_list and self.leave_type=="Without Pay - غير مدفوعة") or (self.leave_type=="Without Pay - غير مدفوعة" and self.total_leave_days >10))):
    #               fl=True




    #       if frappe.session.user==self.owner:
    #           fl=True


    #       if u"Manager" in user_roles and (u"Director" not in user_roles) and frappe.session.user != "Administrator" and self.workflow_state=="Approved By Manager":
    #           fl= True






    #   return fl

    def validate_yearly_repeated_leaves(self):
        if self.leave_type == "New Born - مولود جديد" or self.leave_type == "Death - وفاة" or self.leave_type == "Educational - تعليمية":
            allocation_records = get_leave_allocation_records(self.from_date, self.employee, self.leave_type)
            if allocation_records:
                total_leaves_allocated = allocation_records[self.employee][self.leave_type].total_leaves_allocated
                total_leave_days = get_number_of_leave_days(self.employee, self.leave_type,
                        self.from_date, self.to_date, self.half_day)
                if total_leave_days > total_leaves_allocated/3:
                    frappe.throw(_("{0} days maximum are allowed".format(total_leaves_allocated/3)))

            # lt_max_days = frappe.get_value("Leave Type", filters = {"name": self.leave_type}, fieldname = "max_days_allowed")
            # from_date_year = frappe.utils.data.getdate (self.from_date).year
            # to_date_year = frappe.utils.data.getdate (self.to_date).year

            # total_leave_days = get_number_of_leave_days(self.employee, self.leave_type,
            #       self.from_date, self.to_date, self.half_day)
            # # self.total_leave_days = total_leave_days
            # if total_leave_days != int(lt_max_days):
            #   frappe.throw(_("The total leave days must be exactly {0}".format(int(lt_max_days))))

            # if frappe.db.exists("Leave Allocation", {"employee": self.employee,
            #       "from_date": "{0}-01-01".format(str(from_date_year)),
            #       "to_date": "{0}-12-31".format(str(from_date_year)),
            #       "leave_type": self.leave_type}):

            #   la_doc = frappe.get_doc("Leave Allocation",{
            #           "employee": self.employee,
            #           "from_date": "{0}-01-01".format(str(from_date_year)),
            #           "to_date": "{0}-12-31".format(str(from_date_year)),
            #           "leave_type": self.leave_type
            #           })
            # # la_doc.new_leaves_allocated = 3
            # # la_doc.save(ignore_permissions=True)
            # # frappe.db.commit()

            #   al = get_approved_leaves_for_period(self.employee, self.leave_type, la_doc.from_date, la_doc.to_date)
            #   if self.leave_type == "New Born - مولود جديد" or self.leave_type == "Death - وفاة":
            #       if al >= int(lt_max_days) * 3:
            #           frappe.throw(_("You exceeded the max leave days"))
            #   else:
            #       if al >= int(lt_max_days):
            #           frappe.throw(_("You exceeded the max leave days"))
            #       # frappe.throw("hj")
            #       # la_doc.new_leaves_allocated = int(lt_max_days)
            #       # la_doc.ignore_validate_update_after_submit = True
            #       # la_doc.save(ignore_permissions=True)
            #       # frappe.db.commit()
            # else:
            #   la_doc = frappe.get_doc({
            #           "doctype": "Leave Allocation",
            #           "employee": self.employee,
            #           "from_date": "{0}-01-01".format(str(from_date_year)),
            #           "to_date": "{0}-12-31".format(str(from_date_year)),
            #           "leave_type": self.leave_type,
            #           "new_leaves_allocated" : int(lt_max_days) * 3 if self.leave_type == "New Born - مولود جديد" or self.leave_type == "Death - وفاة"
            #            else int(lt_max_days)
            #           })
            #   la_doc.save(ignore_permissions=True)
            #   la_doc.submit()
            #   frappe.db.commit()

            # # if from_date_year == to_date_year:
            # #     frappe.throw("ll")
            # else:
            #   frappe.throw("ddf")

    # def yearly_hooked_update_leaves_allocated(self):

    #   # frappe.throw(str(frappe.utils.data.nowdate()))
    #   prev_year_date = frappe.utils.data.add_years (frappe.utils.data.nowdate(), -1)
    #   emps = frappe.get_all("Employee",filters = { "status": "Active"}, fields = ["name"])
    #   for emp in emps:
    #       prev_year_allocation_records = get_leave_allocation_records(frappe.utils.data.nowdate(), emp.name, "Annual Leave - اجازة اعتيادية")
    #       if prev_year_allocation_records:
    #           from_date = prev_year_allocation_records[emp.name]["Annual Leave - اجازة اعتيادية"].from_date
    #           to_date = prev_year_allocation_records[emp.name]["Annual Leave - اجازة اعتيادية"].to_date

    #           prev_year_applied_days = get_approved_leaves_for_period(emp.name, "Annual Leave - اجازة اعتيادية", from_date, to_date)
    #           if prev_year_applied_days:
    #               total_leaves_allocated = prev_year_allocation_records[emp.name]["Annual Leave - اجازة اعتيادية"].total_leaves_allocated
    #               if prev_year_applied_days < total_leaves_allocated:
    #                   remain_days = total_leaves_allocated - prev_year_applied_days
    #                   new_allocated_days = remain_days + 30
    #                   if new_allocated_days > 45:
    #                       new_allocated_days = 45
    #                       # frappe.throw(frappe.utils.data.add_years(to_date, +1))
    #                   else:
    #                       new_allocated_days = 30
    #           else:
    #               new_allocated_days = 45
    #       else:
    #           new_allocated_days = 30
    #       su = frappe.new_doc("Leave Allocation")
    #       su.update({
    #           "leave_type": "Annual Leave - اجازة اعتيادية",
    #           "employee": emp.name,
    #           "from_date": frappe.utils.data.add_years(from_date, +1),
    #           "to_date": frappe.utils.data.add_years(to_date, +1),
    #           "new_leaves_allocated": new_allocated_days
    #           })
    #       su.save(ignore_permissions=True)
    #       su.submit()
    #       frappe.db.commit()
                    # if su:
                    # frappe.throw(str(su))
    def validate_monthly_leave(self):
        from frappe.utils import getdate
        # prev_year_date = frappe.utils.data.add_years (self.from_date, -1)
        # # frappe.utils.data.get_first_day (dt, d_years=0, d_months=0)
        # prev_year_allocation_records = get_leave_allocation_records(self.from_date, self.employee, self.leave_type)
        # if prev_year_allocation_records:
        #   prev_year_applied_days = get_approved_leaves_for_period(self.employee, self.leave_type, prev_year_allocation_records[self.employee][self.leave_type].from_date, prev_year_allocation_records[self.employee][self.leave_type].to_date)
        #   if prev_year_applied_days < prev_year_allocation_records[self.employee][self.leave_type].total_leaves_allocated
        # frappe.throw(str(prev_year_date))
        if self.leave_type == "Annual Leave - اجازة اعتيادية" or self.leave_type == "Compensatory off - تعويضية":
            allocation_records = get_leave_allocation_records(self.from_date, self.employee, self.leave_type)
            if allocation_records:
                from_date = allocation_records[self.employee][self.leave_type].from_date
                applied_days = get_approved_leaves_for_period(self.employee, self.leave_type, from_date, self.to_date)

                prev_year_date = frappe.utils.data.add_years(self.from_date, -1)
                prev_year_allocation_records = get_leave_allocation_records(prev_year_date, self.employee, "Annual Leave - اجازة اعتيادية")
                if prev_year_allocation_records:
                    from_date = prev_year_allocation_records[self.employee]["Annual Leave - اجازة اعتيادية"].from_date
                    to_date = prev_year_allocation_records[self.employee]["Annual Leave - اجازة اعتيادية"].to_date
                    prev_year_total_leaves_allocated = prev_year_allocation_records[self.employee]["Annual Leave - اجازة اعتيادية"].total_leaves_allocated
                    prev_year_applied_days = get_approved_leaves_for_period(self.employee, "Annual Leave - اجازة اعتيادية", from_date, to_date)
                    prev_year_remain_balance = prev_year_total_leaves_allocated - prev_year_applied_days
                else:
                    prev_year_remain_balance = 0
                date_dif = date_diff(self.to_date, from_date)
                period_balance = (date_dif) * (allocation_records[self.employee][self.leave_type].total_leaves_allocated/360)+prev_year_remain_balance
                if period_balance > 33:
                    period_balance=33
                # if period_balance < applied_days + self.total_leave_days:
                if self.total_leave_days>self.leave_balance:
                    frappe.throw(_("Your monthly leave balance is not sufficient"))

    def before_submit(self):
        pass

    def validate_back_days(self):
        pass
        # from frappe.utils import getdate, nowdate
        # user = frappe.session.user
        # if getdate(self.from_date) < getdate(nowdate()) and ("HR User" not in frappe.get_roles(user)):

        #   # if user != self.leave_approver:
        #   frappe.throw(_("Application can not be marked for past of the day"))

    def on_update(self):
        pass
        # if (not self.previous_doc and self.leave_approver) or (self.previous_doc and \
        #       self.status == "Open" and self.previous_doc.leave_approver != self.leave_approver):
        #   # notify leave approver about creation

        # if self.previous_doc and self.workflow_state and self.previous_doc.status != self.workflow_state and self.status == "Rejected":
        #   # notify employee about rejection
        #   if self.half_day != 1 :
        #       self.notify_employee(self.status)



    def on_submit(self):
        pass
        #frappe.db.sql("update tabCommunication set subject ='Approved By Manager' , content='Approved By Manager' where reference_name ='{0}' and subject ='Approved By Line Manager'".format(self.name))

        # self.validate_type()
        # self.validate_days_and_fin()
        # if self.half_day != 1 :
        #   # self.notify_exec_manager()
        #   self.notify_employee(self.status)
        # # self.validate_leave_submission_dates()

    def on_update_after_submit(self):
        pass
        #frappe.db.sql("update tabCommunication set subject ='Approved By Manager' , content='Approved By Manager' where reference_name ='{0}' and subject ='Approved By Line Manager'".format(self.name))

        # self.validate_type()
        # self.validate_days_and_fin()

        # if self.half_day != 1 :
        #   # self.notify_exec_manager()
        #   self.notify_employee(self.status)


    def on_cancel(self):
        pass
        # notify leave applier about cancellation
        # if 'Rejected' in self.workflow_state:
        #   frappe.db.sql("update `tabLeave Application` set status ='Rejected' where name ='{0}'".format(self.name))


        # if self.half_day != 1 :
        #   self.notify_employee("cancelled")

    def validate_dates(self):
        if self.from_date and self.to_date and (getdate(self.to_date) < getdate(self.from_date)):
            frappe.throw(_("To date cannot be before from date"))

        if not is_lwp(self.leave_type):
            self.validate_dates_acorss_allocation()
            self.validate_back_dated_application()

    def validate_dates_acorss_allocation(self):
        def _get_leave_alloction_record(date):
            allocation = frappe.db.sql("""select name from `tabLeave Allocation`
                where employee=%s and leave_type=%s and docstatus=1
                and %s between from_date and to_date""", (self.employee, self.leave_type, date))

            return allocation and allocation[0][0]

        allocation_based_on_from_date = _get_leave_alloction_record(self.from_date)
        allocation_based_on_to_date = _get_leave_alloction_record(self.to_date)

        if not (allocation_based_on_from_date or allocation_based_on_to_date):
            frappe.throw(_("Application period cannot be outside leave allocation period"))

        elif allocation_based_on_from_date != allocation_based_on_to_date:
            frappe.throw(_("Application period cannot be across two allocation records"))

    def validate_back_dated_application(self):
        future_allocation = frappe.db.sql("""select name, from_date from `tabLeave Allocation`
            where employee=%s and leave_type=%s and docstatus=1 and from_date > %s
            and carry_forward=1""", (self.employee, self.leave_type, self.to_date), as_dict=1)

        # if future_allocation:
        #     frappe.throw(_("Leave cannot be applied/cancelled before {0}, as leave balance has already been carry-forwarded in the future leave allocation record {1}")
        #         .format(formatdate(future_allocation[0].from_date), future_allocation[0].name))

    def validate_salary_processed_days(self):
        if not frappe.db.get_value("Leave Type", self.leave_type, "is_lwp"):
            return

        last_processed_pay_slip = frappe.db.sql("""
            select start_date, end_date from `tabSalary Slip`
            where docstatus = 1 and employee = %s
            and ((%s between start_date and end_date) or (%s between start_date and end_date))
            order by modified desc limit 1
        """,(self.employee, self.to_date, self.from_date))

        if last_processed_pay_slip:
            frappe.throw(_("Salary already processed for period between {0} and {1}, Leave application period cannot be between this date range.").format(formatdate(last_processed_pay_slip[0][0]),
                formatdate(last_processed_pay_slip[0][1])))


    def show_block_day_warning(self):
        block_dates = get_applicable_block_dates(self.from_date, self.to_date,
            self.employee, self.company, all_lists=True)

        if block_dates:
            frappe.msgprint(_("Warning: Leave application contains following block dates") + ":")
            for d in block_dates:
                frappe.msgprint(formatdate(d.block_date) + ": " + d.reason)

    def validate_block_days(self):
        block_dates = get_applicable_block_dates(self.from_date, self.to_date,
            self.employee, self.company)

        if block_dates and self.status == "Approved":
            frappe.throw(_("You are not authorized to approve leaves on Block Dates"), LeaveDayBlockedError)

    def validate_balance_leaves(self):
        if self.from_date and self.to_date:
            if self.half_day != 1:
                self.total_leave_days = get_number_of_leave_days(self.employee, self.leave_type,
                    self.from_date, self.to_date, self.half_day)
                self.remaining_leave_days = flt(self.leave_balance)-flt(self.total_leave_days)

            if self.total_leave_days == 0:
                frappe.throw(_("The day(s) on which you are applying for leave are holidays. You need not apply for leave."))

            if not is_lwp(self.leave_type):
                self.leave_balance = get_leave_balance_on(self.employee, self.leave_type, self.from_date,
                    consider_all_leaves_in_the_allocation_period=True)

                if self.status != "Rejected" and self.leave_balance < self.total_leave_days:
                    if frappe.db.get_value("Leave Type", self.leave_type, "allow_negative"):
                        frappe.msgprint(_("Note: There is not enough leave balance for Leave Type {0}")
                            .format(self.leave_type))
                    else:
                        frappe.throw(_("There is not enough leave balance for Leave Type {0}")
                            .format(self.leave_type))

    def validate_leave_overlap(self):
        if not self.name:
            # hack! if name is null, it could cause problems with !=
            self.name = "New Leave Application"

        for d in frappe.db.sql("""select name, leave_type, posting_date, from_date, to_date, total_leave_days
            from `tabLeave Application`
            where employee = %(employee)s and docstatus = 1 and status in ("Open", "Approved")
            and to_date >= %(from_date)s and from_date <= %(to_date)s
            and name != %(name)s""", {
                "employee": self.employee,
                "from_date": self.from_date,
                "to_date": self.to_date,
                "name": self.name
            }, as_dict = 1):

            if d['total_leave_days']==0.5 and cint(self.half_day)==1:
                sum_leave_days = self.get_total_leaves_on_half_day()
                if sum_leave_days==1:
                    self.throw_overlap_error(d)
            else:
                self.throw_overlap_error(d)

    def throw_overlap_error(self, d):
        msg = _("Employee {0} has already applied for {1} between {2} and {3}").format(self.employee,
            d['leave_type'], formatdate(d['from_date']), formatdate(d['to_date'])) \
            + """ <br><b><a href="#Form/Leave Application/{0}">{0}</a></b>""".format(d["name"])
        frappe.throw(msg, OverlapError)

    def get_total_leaves_on_half_day(self):
        return frappe.db.sql("""select sum(total_leave_days) from `tabLeave Application`
            where employee = %(employee)s
            and docstatus = 1
            and status in ("Open", "Approved")
            and from_date = %(from_date)s
            and to_date = %(to_date)s
            and name != %(name)s""", {
                "employee": self.employee,
                "from_date": self.from_date,
                "to_date": self.to_date,
                "name": self.name
            })[0][0]

    def validate_max_days(self):
        max_days = frappe.db.get_value("Leave Type", self.leave_type, "max_days_allowed")
        if max_days and self.total_leave_days > cint(max_days):
            frappe.throw(_("Leave of type {0} cannot be longer than {1}").format(self.leave_type, max_days))

    def validate_leave_approver(self):
        employee = frappe.get_doc("Employee", self.employee)
        leave_approvers = [l.leave_approver for l in employee.get("leave_approvers")]

        if len(leave_approvers) and self.leave_approver not in leave_approvers:
            frappe.throw(_("Leave approver must be one of {0}")
                .format(comma_or(leave_approvers)), InvalidLeaveApproverError)

        #~ elif self.leave_approver and not frappe.db.sql("""select name from `tabUserRole`
            #~ where parent=%s and role='Leave Approver'""", self.leave_approver):
            #~ frappe.throw(_("{0} ({1}) must have role 'Leave Approver'")\
                #~ .format(get_fullname(self.leave_approver), self.leave_approver), InvalidLeaveApproverError)

        elif self.docstatus==1 and employee.reports_to and self.leave_approver != frappe.session.user:
            frappe.throw(_("Only the selected Leave Approver can submit this Leave Application"),
                LeaveApproverIdentityError)

    def validate_attendance(self):
        attendance = frappe.db.sql("""select name from `tabAttendance` where employee = %s and (att_date between %s and %s)
                    and status = "Present" and docstatus = 1""",
            (self.employee, self.from_date, self.to_date))
        if attendance:
            frappe.throw(_("Attendance for employee {0} is already marked for this day").format(self.employee),
                AttendanceAlreadyMarkedError)

    def notify_employee(self, status):
        employee = frappe.get_doc("Employee", self.employee)
        if not employee.user_id:
            return

        def _get_message(url=False):
            if url:
                name = get_link_to_form(self.doctype, self.name)
            else:
                name = self.name

            message = "Leave Application: {name}".format(name=name)+"<br>"
            if self.workflow_state:
                message += "Workflow State: {workflow_state}".format(workflow_state=self.workflow_state)+"<br>"
            message += "Leave Type: {leave_type}".format(leave_type=self.leave_type)+"<br>"
            message += "From Date: {from_date}".format(from_date=self.from_date)+"<br>"
            message += "To Date: {to_date}".format(to_date=self.to_date)+"<br>"
            message += "Status: {status}".format(status=_(status))
            return message

        def _get_sms(url=False):
            name = self.name
            employee_name = cstr(employee.employee_name)
            message = (_("%s") % (name))
            if self.workflow_state:
                message += "{workflow_state}".format(workflow_state=self.workflow_state)+"\n"
            message += (_("%s") % (employee_name))+"\n"
            message += (_("%s") % (self.leave_type))+"\n"
            message += (_("%s") % (self.from_date))+"\n"
            return message

        try:
            self.notify({
                # for post in messages
                "message": _get_message(url=True),
                "message_to": employee.prefered_email,
                "subject": (_("Leave Application") + ": %s - %s") % (self.name, _(status))
            })
        except:
            frappe.throw("could not send")

        #~ send_sms([employee.cell_number], cstr(_get_sms(url=False)))

    def notify_leave_approver(self):
        employee = frappe.get_doc("Employee", self.employee)

        def _get_message(url=False):
            name = self.name
            employee_name = cstr(employee.employee_name)
            if url:
                name = get_link_to_form(self.doctype, self.name)
                employee_name = get_link_to_form("Employee", self.employee, label=employee_name)
            message = (_("Leave Application") + ": %s") % (name)+"<br>"
            if self.workflow_state:
                message += "Workflow State: {workflow_state}".format(workflow_state=self.workflow_state)+"<br>"
            message += (_("Employee") + ": %s") % (employee_name)+"<br>"
            message += (_("Leave Type") + ": %s") % (self.leave_type)+"<br>"
            message += (_("From Date") + ": %s") % (self.from_date)+"<br>"
            message += (_("To Date") + ": %s") % (self.to_date)
            return message
        def _get_sms(url=False):
            name = self.name
            employee_name = cstr(employee.employee_name)
            message = (_("%s") % (name))
            if self.workflow_state:
                message += "{workflow_state}".format(workflow_state=self.workflow_state)+"\n"
            message += (_("%s") % (employee_name))+"\n"
            message += (_("%s") % (self.leave_type))+"\n"
            message += (_("%s") % (self.from_date))+"\n"
            return message

        self.notify({
            # for post in messages
            "message": _get_message(url=True),
            "message_to": frappe.session.user,

            # for email
            "subject": (_("New Leave Application") + ": %s - " + _("Employee") + ": %s") % (self.name, cstr(employee.employee_name))
        })
        try :
            pass
            # la = frappe.get_doc("Employee", {"user_id":self.leave_approver})
            #~ send_sms([la.cell_number], cstr(_get_sms(url=False)))
        except:
            pass

    def notify_exec_manager(self):
        employee = frappe.get_doc("Employee", self.employee)
        super_emp_list = []
        supers =frappe.get_all('UserRole', fields = ["parent"], filters={'role' : 'Executive Manager'})

        for s in supers:
            super_emp_list.append(s.parent)
        try:super_emp_list.remove('Administrator')
        except : pass

        def _get_message(url=False):
            name = self.name
            employee_name = cstr(employee.employee_name)
            if url:
                name = get_link_to_form(self.doctype, self.name)
                employee_name = get_link_to_form("Employee", self.employee, label=employee_name)
            message = (_("Leave Application") + ": %s") % (name)+"<br>"
            if self.workflow_state:
                message += "Workflow State: {workflow_state}".format(workflow_state=self.workflow_state)+"<br>"
            message += (_("Employee") + ": %s") % (employee_name)+"<br>"
            message += (_("Leave Type") + ": %s") % (self.leave_type)+"<br>"
            message += (_("From Date") + ": %s") % (self.from_date)+"<br>"
            message += (_("To Date") + ": %s") % (self.to_date)
            return message
        def _get_sms(url=False):
            name = self.name
            employee_name = cstr(employee.employee_name)
            message = (_("%s") % (name))
            if self.workflow_state:
                message += "{workflow_state}".format(workflow_state=self.workflow_state)+"\n"
            message += (_("%s") % (employee_name))+"\n"
            message += (_("%s") % (self.leave_type))+"\n"
            message += (_("%s") % (self.from_date))+"\n"
            return message

        cells = []
        emp_result =frappe.get_all('Employee', fields = ["cell_number"], filters = [["user_id", "in", super_emp_list]])
        for emp in emp_result:
            cells.append(emp.cell_number)

        if emp_result:
            pass
            #send_sms(cells, cstr(_get_sms(url=False)))

        for s in super_emp_list:
            self.notify({
                # for post in messages
                "message": _get_message(url=True),
                "message_to": s,
                # for email
                "subject": (_("New Leave Application") + ": %s - " + _("Employee") + ": %s") % (self.name, cstr(employee.employee_name))
            })

    def notify(self, args):
        args = frappe._dict(args)
        from frappe.desk.page.chat.chat import post
        post(**{"txt": args.message, "contact": args.message_to, "subject": args.subject,
            "notify": cint(self.follow_via_email)})
def insert_department():
    las = frappe.db.sql("select name, employee from `tabLeave Application` where department is null", as_dict=True)
    for la in las:
        dep = frappe.get_value("Employee", filters = {"name": la.employee}, fieldname="department")
        nla = frappe.get_doc("Leave Application", la.name)
        nla.flags.ignore_validate_update_after_submit=True
        nla.set("department", dep)
        nla.save()
        print la.name

@frappe.whitelist()
def get_approvers(doctype, txt, searchfield, start, page_len, filters):
    if not filters.get("employee"):
        frappe.throw(_("Please select Employee Record first."))

    employee_user = frappe.get_value("Employee", filters.get("employee"), "user_id")

    approvers_list = frappe.db.sql("""select user.name, user.first_name, user.last_name from
        tabUser user, `tabEmployee Leave Approver` approver where
        approver.parent = %s
        and user.name like %s
        and approver.leave_approver=user.name""", (filters.get("employee"), "%" + txt + "%"))

    #~ if not approvers_list:
        #~ approvers_list = get_approver_list(employee_user)
    return approvers_list

@frappe.whitelist()
def get_monthly_accumulated_leave(from_date, to_date, leave_type, employee, for_report=True):
    emp = frappe.get_doc('Employee', employee)

    allocation_records = get_leave_allocation_records(from_date, employee, leave_type)
    if allocation_records:
        applied_days = get_approved_leaves_for_period(employee, leave_type, allocation_records[employee][leave_type].from_date, to_date)

        if for_report:
            total_leave_days=0
        else:
            total_leave_days = get_number_of_leave_days(employee, leave_type, from_date, to_date)

        date_dif = date_diff(to_date, allocation_records[employee][leave_type].from_date)
        balance = ""
        if leave_type == "Annual Leave - اجازة اعتيادية":
            # al_from_date_month = getdate(allocation_records[employee][leave_type].from_date).month
            # al_to_date_month = getdate(allocation_records[employee][leave_type].to_date).month
            # frappe.throw(str(date_dif))

            prev_year_date = frappe.utils.data.add_years(from_date, -1)
            prev_year_allocation_records = get_leave_allocation_records(prev_year_date, employee, "Annual Leave - اجازة اعتيادية")
            if prev_year_allocation_records:
                from_date = prev_year_allocation_records[employee]["Annual Leave - اجازة اعتيادية"].from_date
                to_date = prev_year_allocation_records[employee]["Annual Leave - اجازة اعتيادية"].to_date
                prev_year_total_leaves_allocated = prev_year_allocation_records[employee]["Annual Leave - اجازة اعتيادية"].total_leaves_allocated
                prev_year_applied_days = get_approved_leaves_for_period(employee, "Annual Leave - اجازة اعتيادية", from_date, to_date)
                prev_year_remain_balance = prev_year_total_leaves_allocated - prev_year_applied_days
                if prev_year_remain_balance >= 33: #UPDATE MSH 11
                    prev_year_remain_balance = 33  #UPDATE MSH 11
            else:
                prev_year_remain_balance = 0
            # frappe.throw(str((date_dif) * (22/360)))

            period_balance = ((date_dif-emp.truncated_days) * (0.0603)) + prev_year_remain_balance
            # frappe.msgprint(str(prev_year_remain_balance))
            # frappe.msgprint(str(date_dif))
            # frappe.msgprint(str(emp.truncated_days))
            # frappe.msgprint(str(period_balance))
            # frappe.msgprint(str(applied_days))
            # frappe.msgprint(str(total_leave_days))
            # if period_balance > 33:
            #     period_balance=33
            balance = period_balance - applied_days - total_leave_days

            if balance > 33:
                balance=33

            # getdate(to_date).month

        elif leave_type == "Compensatory off - تعويضية":
            al_from_date = getdate(allocation_records[employee][leave_type].from_date)
            first_of_month = 1 if al_from_date.day == 1 else 0

            if al_from_date.year == getdate(to_date).year:
                period_balance = (getdate(to_date).month - al_from_date.month + first_of_month)*10
                balance = period_balance - applied_days - total_leave_days

            elif al_from_date.year < getdate(to_date).year:
                period_balance = (12 - al_from_date.month + getdate(to_date).month + first_of_month)*10
                balance = period_balance - applied_days - total_leave_days
            else:
                frappe.throw(_("Invalid Dates"))

        return str(balance)





@frappe.whitelist()
def get_monthly_actual_accumulated_leave(from_date, to_date, leave_type, employee, for_report=True):
    emp = frappe.get_doc('Employee', employee)

    allocation_records = get_leave_allocation_records(from_date, employee, leave_type)
    if allocation_records:
        applied_days = get_approved_leaves_for_period(employee, leave_type, allocation_records[employee][leave_type].from_date, to_date)

        if for_report:
            total_leave_days=0
        else:
            total_leave_days = get_number_of_leave_days(employee, leave_type, from_date, to_date)

        date_dif = date_diff(to_date, allocation_records[employee][leave_type].from_date)
        balance = ""
        if leave_type == "Annual Leave - اجازة اعتيادية":
            # al_from_date_month = getdate(allocation_records[employee][leave_type].from_date).month
            # al_to_date_month = getdate(allocation_records[employee][leave_type].to_date).month
            # frappe.throw(str(date_dif))

            prev_year_date = frappe.utils.data.add_years(from_date, -1)
            prev_year_allocation_records = get_leave_allocation_records(prev_year_date, employee, "Annual Leave - اجازة اعتيادية")
            if prev_year_allocation_records:
                from_date = prev_year_allocation_records[employee]["Annual Leave - اجازة اعتيادية"].from_date
                to_date = prev_year_allocation_records[employee]["Annual Leave - اجازة اعتيادية"].to_date
                prev_year_total_leaves_allocated = prev_year_allocation_records[employee]["Annual Leave - اجازة اعتيادية"].total_leaves_allocated
                prev_year_applied_days = get_approved_leaves_for_period(employee, "Annual Leave - اجازة اعتيادية", from_date, to_date)
                prev_year_remain_balance = prev_year_total_leaves_allocated - prev_year_applied_days
                if prev_year_remain_balance >= 33: #UPDATE MSH 11
                    prev_year_remain_balance = 33  #UPDATE MSH 11
            else:
                prev_year_remain_balance = 0
            # frappe.throw(str((date_dif) * (22/360)))

            period_balance = ((date_dif-emp.truncated_days) * (0.0603)) + prev_year_remain_balance
            balance = period_balance - applied_days - total_leave_days

            # getdate(to_date).month

        elif leave_type == "Compensatory off - تعويضية":
            al_from_date = getdate(allocation_records[employee][leave_type].from_date)
            first_of_month = 1 if al_from_date.day == 1 else 0

            if al_from_date.year == getdate(to_date).year:
                period_balance = (getdate(to_date).month - al_from_date.month + first_of_month)*10
                balance = period_balance - applied_days - total_leave_days

            elif al_from_date.year < getdate(to_date).year:
                period_balance = (12 - al_from_date.month + getdate(to_date).month + first_of_month)*10
                balance = period_balance - applied_days - total_leave_days
            else:
                frappe.throw(_("Invalid Dates"))

        return str(balance)


@frappe.whitelist()
def get_number_of_leave_days(employee, leave_type, from_date, to_date, half_day=None):
    if half_day==1:
        return
    number_of_days = date_diff(to_date, from_date) + 1
    if not frappe.db.get_value("Leave Type", leave_type, "include_holiday"):
        number_of_days = flt(number_of_days) - flt(get_holidays(employee, from_date, to_date))

    return number_of_days

@frappe.whitelist()
def get_leave_balance_on(employee, leave_type, date, allocation_records=None,
        consider_all_leaves_in_the_allocation_period=False):
    if allocation_records == None:
        allocation_records = get_leave_allocation_records(date, employee).get(employee, frappe._dict())

    allocation = allocation_records.get(leave_type, frappe._dict())

    if consider_all_leaves_in_the_allocation_period:
        date = allocation.to_date
    leaves_taken = get_approved_leaves_for_period(employee, leave_type, allocation.from_date, date)

    return flt(allocation.total_leaves_allocated) - flt(leaves_taken)
def has_approved_leave(leave_type, employee):
    la = frappe.db.sql("""select name from `tabLeave Application`
        where leave_type = '{0}' and docstatus = 1 and status='Approved'
        and employee = '{1}'""".format(leave_type, employee))
    return True if la else False

def get_approved_leaves_for_period(employee, leave_type, from_date, to_date):
    #"
    leave_applications = frappe.db.sql("""
        select name,employee, leave_type, from_date, to_date, total_leave_days
        from `tabLeave Application`
        where employee=%(employee)s and leave_type=%(leave_type)s
            and docstatus=1 and status='Approved'
            and (from_date between %(from_date)s and %(to_date)s
                or to_date between %(from_date)s and %(to_date)s
                or (from_date < %(from_date)s and to_date > %(to_date)s))
    """, {
        "from_date": from_date,
        "to_date": to_date,
        "employee": employee,
        "leave_type": leave_type
    }, as_dict=1)

    leave_days = 0
    for leave_app in leave_applications:
        leave_days += leave_app.total_leave_days
        # if leave_app.from_date >= getdate(from_date) and leave_app.to_date <= getdate(to_date):
        #     return_from_leave = frappe.db.sql(""" select name,from_date,return_date from `tabReturn From Leave Statement` where leave_application='{0}' and docstatus=1""".format(leave_app.name), as_dict=1)
        #     if return_from_leave and len(return_from_leave) > 0:
        #         leave_days += date_diff(return_from_leave[0].return_date,return_from_leave[0].from_date) + 1
        #     else:
        #         leave_days += leave_app.total_leave_days
        # else:
        #     if leave_app.from_date < getdate(from_date):
        #         leave_app.from_date = from_date
        #     if leave_app.to_date > getdate(to_date):
        #         leave_app.to_date = to_date
        #     return_from_leave = frappe.db.sql(""" select name,from_date,return_date from `tabReturn From Leave Statement` where leave_application='{0}' and docstatus=1""".format(leave_app.name), as_dict=1)
        #     if return_from_leave and len(return_from_leave) > 0:
        #         leave_days += date_diff(return_from_leave[0].return_date,return_from_leave[0].from_date) + 1
        #     else:
        #         leave_days += get_number_of_leave_days(employee, leave_type,
        #             leave_app.from_date, leave_app.to_date)

    return leave_days

def get_leave_allocation_records(date, employee=None, leave_type=None):
    conditions = (" and employee='%s'" % employee) if employee else ""
    conditions += (" and leave_type='%s'" % leave_type) if leave_type else ""
    leave_allocation_records = frappe.db.sql("""
        select employee, leave_type, total_leaves_allocated, from_date, to_date
        from `tabLeave Allocation`
        where %s between from_date and to_date and docstatus=1 {0}""".format(conditions), (date), as_dict=1)

    allocated_leaves = frappe._dict()
    for d in leave_allocation_records:
        allocated_leaves.setdefault(d.employee, frappe._dict()).setdefault(d.leave_type, frappe._dict({
            "from_date": d.from_date,
            "to_date": d.to_date,
            "total_leaves_allocated": d.total_leaves_allocated
        }))

    return allocated_leaves

@frappe.whitelist()
def get_holidays(employee, from_date, to_date):
    '''get holidays between two dates for the given employee'''
    holiday_list = get_holiday_list_for_employee(employee)

    holidays = frappe.db.sql("""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
        where h1.parent = h2.name and h1.holiday_date between %s and %s
        and h2.name = %s""", (from_date, to_date, holiday_list))[0][0]

    return holidays

def is_lwp(leave_type):
    lwp = frappe.db.sql("select is_lwp from `tabLeave Type` where name = %s", leave_type)
    return lwp and cint(lwp[0][0]) or 0

@frappe.whitelist()
def get_events(start, end):
    events = []

    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, ["name", "company"],
        as_dict=True)
    if employee:
        employee, company = employee.name, employee.company
    else:
        employee=''
        company=frappe.db.get_value("Global Defaults", None, "default_company")

    from frappe.desk.reportview import build_match_conditions
    match_conditions = build_match_conditions("Leave Application")

    # show department leaves for employee
    if "Employee" in frappe.get_roles():
        add_department_leaves(events, start, end, employee, company)

    add_leaves(events, start, end, match_conditions)

    add_block_dates(events, start, end, employee, company)
    add_holidays(events, start, end, employee, company)

    return events

def add_department_leaves(events, start, end, employee, company):
    department = frappe.db.get_value("Employee", employee, "department")

    if not department:
        return

    # department leaves
    department_employees = frappe.db.sql_list("""select name from tabEmployee where department=%s
        and company=%s""", (department, company))

    match_conditions = "employee in (\"%s\")" % '", "'.join(department_employees)
    add_leaves(events, start, end, match_conditions=match_conditions)

def add_leaves(events, start, end, match_conditions=None):
    query = """select name, from_date, to_date, employee_name, half_day,
        status, employee, docstatus
        from `tabLeave Application` where
        from_date <= %(end)s and to_date >= %(start)s <= to_date
        and docstatus < 2
        and status!="Rejected" """
    if match_conditions:
        query += " and " + match_conditions

    for d in frappe.db.sql(query, {"start":start, "end": end}, as_dict=True):
        e = {
            "name": d.name,
            "doctype": "Leave Application",
            "from_date": d.from_date,
            "to_date": d.to_date,
            "status": d.status,
            "title": cstr(d.employee_name) + \
                (d.half_day and _(" (Half Day)") or ""),
            "docstatus": d.docstatus
        }
        if e not in events:
            events.append(e)

def add_block_dates(events, start, end, employee, company):
    # block days
    from erpnext.hr.doctype.leave_block_list.leave_block_list import get_applicable_block_dates

    cnt = 0
    block_dates = get_applicable_block_dates(start, end, employee, company, all_lists=True)

    for block_date in block_dates:
        events.append({
            "doctype": "Leave Block List Date",
            "from_date": block_date.block_date,
            "to_date": block_date.block_date,
            "title": _("Leave Blocked") + ": " + block_date.reason,
            "name": "_" + str(cnt),
        })
        cnt+=1

def add_holidays(events, start, end, employee, company):
    applicable_holiday_list = get_holiday_list_for_employee(employee, company)
    if not applicable_holiday_list:
        return

    for holiday in frappe.db.sql("""select name, holiday_date, description
        from `tabHoliday` where parent=%s and holiday_date between %s and %s""",
        (applicable_holiday_list, start, end), as_dict=True):
            events.append({
                "doctype": "Holiday",
                "from_date": holiday.holiday_date,
                "to_date":  holiday.holiday_date,
                "title": _("Holiday") + ": " + cstr(holiday.description),
                "name": holiday.name
            })

def hooked_leave_allocation_builder():
    # , "Annual Leave - اجازة اعتيادية"
    # prev_year_date = frappe.utils.data.add_years (frappe.utils.data.nowdate(), -1)
        emps = frappe.get_all("Employee",filters = {"status": "Active"}, fields = ["name", "date_of_joining"])
        for emp in emps:
            if 'EMP/1' in emp.name or emp.name=='EMP/2007':
            # if 'EMP/1021' == emp.name:
                lts = frappe.get_list("Leave Type", fields = ["name"])
                for lt in lts:
                    allocation_records = get_leave_allocation_records(nowdate(), emp.name, lt.name)

                    if not allocation_records:
                        allocation_from_date = ""
                        allocation_to_date = ""
                        new_leaves_allocated = 0
                        if getdate(add_years(emp.date_of_joining,1)) > getdate(nowdate()):
                            allocation_from_date = emp.date_of_joining
                            allocation_to_date = add_days(add_years(emp.date_of_joining,1),-1)
                            # if emp.name == "EMP/1007":
                            #   print("sssss"  "  " + allocation_from_date)
                        else:
                            day = "0" + str(getdate(emp.date_of_joining).day) if len(str(getdate(emp.date_of_joining).day)) == 1 else str(getdate(emp.date_of_joining).day)
                            month = "0" + str(getdate(emp.date_of_joining).month) if len(str(getdate(emp.date_of_joining).month)) == 1 else str(getdate(emp.date_of_joining).month)
                            year = str(getdate(nowdate()).year)
                            allocation_from_date = year + "-" + month + "-" + day
                            allocation_to_date = add_days(add_years(allocation_from_date,1),-1)
                            # if emp.name == "EMP/1007":
                            #   print("mmmmm"+ "  " + allocation_from_date)

                        if lt.name == "Annual Leave - اجازة اعتيادية":
                            # if getdate(nowdate()) > getdate(add_months(emp.date_of_joining,3)):
                            prev_year_date = frappe.utils.data.add_years(frappe.utils.data.nowdate(), -1)
                            prev_year_allocation_records = get_leave_allocation_records(prev_year_date, emp.name, "Annual Leave - اجازة اعتيادية")
                            if prev_year_allocation_records:
                                from_date = prev_year_allocation_records[emp.name]["Annual Leave - اجازة اعتيادية"].from_date
                                to_date = prev_year_allocation_records[emp.name]["Annual Leave - اجازة اعتيادية"].to_date
                                prev_year_total_leaves_allocated = prev_year_allocation_records[emp.name]["Annual Leave - اجازة اعتيادية"].total_leaves_allocated
                                prev_year_applied_days = get_approved_leaves_for_period(emp.name, "Annual Leave - اجازة اعتيادية", from_date, to_date)

                                if prev_year_total_leaves_allocated == prev_year_applied_days:
                                    if emp.name == 'EMP/1002':
                                        new_leaves_allocated = 0.0713
                                    else:
                                        new_leaves_allocated = 0.0611
                                elif prev_year_total_leaves_allocated > prev_year_applied_days:
                                    remain_days = prev_year_total_leaves_allocated - prev_year_applied_days
                                    #if remain_days >33: #ADD MSH
                                    #    remain_days = 33 #ADD MSH
                                    if emp.name == 'EMP/1002':
                                        new_leaves_allocated = remain_days + 0.0713
                                    else:
                                        new_leaves_allocated = remain_days + 0.0611
                                    print(new_leaves_allocated)
                                    if new_leaves_allocated > 33:
                                        new_leaves_allocated = 33
                            else:
                                new_leaves_allocated = 0.0611

                            print new_leaves_allocated

                            su = frappe.new_doc("Leave Allocation")
                            su.update({
                                "leave_type": "Annual Leave - اجازة اعتيادية",
                                "employee": emp.name,
                                "from_date": allocation_from_date,
                                "to_date": add_years(allocation_to_date,4),
                                "new_leaves_allocated": new_leaves_allocated
                                })
                            su.save(ignore_permissions=True)
                            su.submit()
                            frappe.db.commit()

                        if lt.name == "emergency -اضطرارية":
                            su = frappe.new_doc("Leave Allocation")
                            su.update({
                                    "leave_type": "emergency -اضطرارية",
                                    "employee": emp.name,
                                    "from_date": allocation_from_date,
                                    "to_date": allocation_to_date,
                                    "new_leaves_allocated": 3
                                    })
                            su.save(ignore_permissions=True)
                            su.submit()
                            frappe.db.commit()

                        if lt.name == "New Born - مولود جديد":
                            su = frappe.new_doc("Leave Allocation")
                            su.update({
                                    "leave_type": "New Born - مولود جديد",
                                    "employee": emp.name,
                                    "from_date": allocation_from_date,
                                    "to_date": allocation_to_date,
                                    "new_leaves_allocated": 9
                                    })
                            su.save(ignore_permissions=True)
                            su.submit()
                            frappe.db.commit()

                        if lt.name == "Educational - تعليمية":
                            su = frappe.new_doc("Leave Allocation")
                            su.update({
                                    "leave_type": "Educational - تعليمية",
                                    "employee": emp.name,
                                    "from_date": allocation_from_date,
                                    "to_date": allocation_to_date,
                                    "new_leaves_allocated": 90
                                    })
                            su.save(ignore_permissions=True)
                            su.submit()
                            frappe.db.commit()

                        if lt.name == "Death - وفاة":
                            su = frappe.new_doc("Leave Allocation")
                            su.update({
                                    "leave_type": "Death - وفاة",
                                    "employee": emp.name,
                                    "from_date": allocation_from_date,
                                    "to_date": allocation_to_date,
                                    "new_leaves_allocated": 15
                                    })
                            su.save(ignore_permissions=True)
                            su.submit()
                            frappe.db.commit()

                        if lt.name == "Hajj leave - حج":
                            su = frappe.new_doc("Leave Allocation")
                            su.update({
                                        "leave_type": "Hajj leave - حج",
                                        "employee": emp.name,
                                        "from_date": allocation_from_date,
                                        "to_date": allocation_to_date,
                                        "new_leaves_allocated": 15
                                        })
                            su.save(ignore_permissions=True)
                            su.submit()
                            frappe.db.commit()

                        if lt.name == "Marriage - زواج":
                            su = frappe.new_doc("Leave Allocation")
                            su.update({
                                        "leave_type": "Marriage - زواج",
                                        "employee": emp.name,
                                        "from_date": allocation_from_date,
                                        "to_date": allocation_to_date,
                                        "new_leaves_allocated": 5
                                        })
                            su.save(ignore_permissions=True)
                            su.submit()
                            frappe.db.commit()

                        if lt.name == "Sick Leave - مرضية":
                            su = frappe.new_doc("Leave Allocation")
                            su.update({
                                        "leave_type": "Sick Leave - مرضية",
                                        "employee": emp.name,
                                        "from_date": allocation_from_date,
                                        "to_date": allocation_to_date,
                                        "new_leaves_allocated": 150
                                        })
                            su.save(ignore_permissions=True)
                            su.submit()
                            frappe.db.commit()

                        if lt.name == "Compensatory off - تعويضية":
                            su = frappe.new_doc("Leave Allocation")
                            su.update({
                                        "leave_type": "Compensatory off - تعويضية",
                                        "employee": emp.name,
                                        "from_date": allocation_from_date,
                                        "to_date": allocation_to_date,
                                        "new_leaves_allocated": 120
                                        })
                            su.save(ignore_permissions=True)
                            su.submit()
                            frappe.db.commit()


                        # frappe.utils.data.getdate(frappe.utils.data.nowdate()).month
                        # if lt.name not in ('Without Pay - غير مدفوعة'):
                            # print lt.name + "--" + emp.name


                    # from_date = prev_year_allocation_records[emp.name]["Annual Leave - اجازة اعتيادية"].from_date
                    # to_date = prev_year_allocation_records[emp.name]["Annual Leave - اجازة اعتيادية"].to_date

                    # prev_year_applied_days = get_approved_leaves_for_period(emp.name, "Annual Leave - اجازة اعتيادية", from_date, to_date)

    # lts = frappe.get_list("Leave Type", fields = ["name"])
    # for lt in lts:
    #   print lt.name



def increase_daily_leave_balance():
    emps = frappe.get_all("Employee",filters = {"status": "Active"}, fields = ["name"])
    for emp in emps:
        if 'EMP/1' in emp.name or emp.name=='EMP/2007':
            allocation = frappe.db.sql("select name from `tabLeave Allocation` where leave_type='Annual Leave - اجازة اعتيادية' and employee='{0}' and '{1}' between from_date and to_date order by to_date desc limit 1".format(emp.name,nowdate()))
            if allocation:
                doc = frappe.get_doc('Leave Allocation', allocation[0][0])

                current_year_applied_days = get_approved_leaves_for_period(emp.name, "Annual Leave - اجازة اعتيادية", doc.from_date, doc.to_date)
                current_remain_days = flt(doc.new_leaves_allocated)-flt(current_year_applied_days)

                if emp.name == 'EMP/1002':
                    if current_remain_days < 33.0:
                        if current_remain_days + 0.0713 >= 33.0:
                            leave_balance = current_year_applied_days + 33.0
                        else:
                            leave_balance = doc.new_leaves_allocated + 0.0713
                        doc.new_leaves_allocated = leave_balance
                        doc.save()
                        print("0.0713 -Increase daily leave balance for employee {0}".format(emp.name))
                else:
                    if current_remain_days < 33.0:
                        if current_remain_days + 0.0611 >= 33.0:
                            leave_balance = current_year_applied_days + 33.0
                        else:
                            leave_balance = doc.new_leaves_allocated + 0.0611
                        doc.new_leaves_allocated = leave_balance
                        doc.save()
                        print("0.0611 -Increase daily leave balance for employee {0}".format(emp.name))





def calculate_truncated_days():
    emps = frappe.get_all("Employee",filters = {"status": "Active"}, fields = ["name"])
    for emp in emps:
        if 'EMP/1' in emp.name and emp.name=='EMP/1026':
            allocation_records = get_leave_allocation_records(nowdate(), emp.name, 'Annual Leave - اجازة اعتيادية')

            if allocation_records:
                current_actual_leave_balance =  get_monthly_actual_accumulated_leave(nowdate(),nowdate(),'Annual Leave - اجازة اعتيادية',emp.name)

                current_leave_balance =  get_monthly_accumulated_leave(nowdate(),nowdate(),'Annual Leave - اجازة اعتيادية',emp.name)

                print current_actual_leave_balance,current_leave_balance

                if flt(current_actual_leave_balance) >= 33.0:
                    employee = frappe.get_doc('Employee', emp.name)
                    employee.truncated_days = employee.truncated_days + 1
                    employee.save()
                    print("Increased extra truncated day for employee {0}".format(emp.name))


def update_la_from_date():
    new_emps = frappe.db.sql("""SELECT `tabLeave Allocation`.name, `tabEmployee`.date_of_joining,
        `tabLeave Allocation`.employee FROM `tabLeave Allocation` INNER JOIN `tabEmployee` ON
        `tabLeave Allocation`.employee =
        `tabEmployee`.name where DATEDIFF('2017-01-01',`tabEmployee`.date_of_joining) < 0
        and `tabLeave Allocation`.leave_type = 'Annual Leave - اجازة اعتيادية' """, as_dict = True)
    for new_emp in new_emps:
        frappe.db.set_value("Leave Allocation", new_emp.name, "from_date", new_emp.date_of_joining)
        print new_emp.date_of_joining

def create_return_from_leave_statement_after_leave():
    ''' Create return form leave docfield at 12 pm when the leave application ends  '''

    lps = frappe.get_list("Leave Application", filters = {"status": "Approved","is_canceled":0}, fields = ["name", "to_date", "from_date", "employee", "employee_name", "department", "total_leave_days"])
    for lp in lps:
        emp_user = frappe.get_value("Employee", filters = {"name": lp.employee}, fieldname = "user_id")
        rfls = frappe.get_value("Return From Leave Statement", filters = {"leave_application": lp.name}, fieldname = ["name"])
        try:
            if not rfls and getdate(nowdate()) == getdate(lp.to_date):
                workflow_state = ""
                if u'CEO' in frappe.get_roles(emp_user):
                    workflow_state = "Created By CEO"
                elif u'Director' in frappe.get_roles(emp_user):
                    workflow_state = "Created By Director"
                elif u'Manager' in frappe.get_roles(emp_user):
                    workflow_state = "Created By Manager"
                elif u'Line Manager' in frappe.get_roles(emp_user):
                    workflow_state = "Created By Line Manager"
                elif u'Employee' in frappe.get_roles(emp_user):
                    workflow_state = "Pending"
                rfls_doc = frappe.get_doc({
                    "doctype": "Return From Leave Statement",
                    "leave_application": lp.name,
                    "employee": lp.employee,
                    "employee_name": lp.employee_name,
                    "owner": emp_user,
                    "total_leave_days": lp.total_leave_days,
                    "from_date": lp.from_date,
                    "to_date": lp.to_date,
                    "workflow_state": workflow_state
                    })
                rfls_doc.flags.ignore_validate = True
                rfls_doc.flags.ignore_mandatory = True
                rfls_doc.save()

                frappe.db.commit()

                from frappe.core.doctype.communication.email import make
                frappe.flags.sent_mail = None
                content_msg="Please review your Return From Leave Statement a new application has been created"
                prefered_email = frappe.get_value("Employee", filters = {"user_id": emp_user}, fieldname = "prefered_email")

                if prefered_email:
                    try:
                        print("Sending Message")
                        make(subject = "Return from leave Statement", content=content_msg, recipients=prefered_email,
                            send_email=True, sender="erp@tawari.sa")
                        print("Sent")
                    except:
                        frappe.msgprint("could not send")
        except frappe.exceptions.CancelledLinkError:
            print("Canceled Document " + lp.name)
            pass
        # print nowdate()



# def get_permission_query_conditions(user):
#     if u'System Manager' in frappe.get_roles(user) or u'HR User' in frappe.get_roles(user):
#         return None

#     elif u'Leave Approver' in frappe.get_roles(user):
#         employee = frappe.get_doc('Employee', {'user_id': user})

#         return """(`tabLeave Application`.leave_approver = '{user}' or `tabLeave Application`.employee = '{employee}')""" \
#             .format(user=frappe.db.escape(user), employee=frappe.db.escape(employee.name))

#     elif u'Employee' in frappe.get_roles(user):
#         employee = frappe.get_doc('Employee', {'user_id': user})

#         return """(`tabLeave Application`.owner = '{user}' or `tabLeave Application`.employee = '{employee}')""" \
#             .format(user=frappe.db.escape(user), employee=frappe.db.escape(employee.name))
def has_permission(doc):
    if frappe.session.user == "fa.alghurais@tawari.sa":
        return True


def get_permission_query_conditions(user):
    if frappe.session.user == "fa.alghurais@tawari.sa":
        query = """(True) or (True)"""
        return query
    # if not user: user = frappe.session.user
    # employees = frappe.get_list("Employee", fields=["name"], filters={'user_id': user}, ignore_permissions=True)
    # if employees:
    #   employee = frappe.get_doc('Employee', {'name': employees[0].name})

    #   if employee:
    #       query = ""

    #       if u'CEO' in frappe.get_roles(user) :
    #           if query != "":
    #               query+=" or "
    #           query+= "`tabLeave Application`.workflow_state = 'Created By Director' or(`tabLeave Application`.workflow_state = 'Approved By Director' and (`tabLeave Application`.leave_type = 'Without Pay - غير مدفوعة' or (`tabLeave Application`.leave_type='Annual Leave - اجازة اعتيادية' and `tabLeave Application`.total_leave_days>=30)))"

    #       if u'Director' in frappe.get_roles(user):
    #           if query != "":
    #               query+=" or "
    #           department = frappe.get_value("Department" , filters= {"director": employee.name}, fieldname="name")
    #           query+="""(employee in (SELECT name from tabEmployee where tabEmployee.department = '{0}')  or employee = '{1}')""".format(department, employee.name)

    #       if u'Manager' in frappe.get_roles(user):
    #           if query != "":
    #               query+=" or "
    #           department = frappe.get_value("Department" , filters= {"manager": employee.name}, fieldname="name")
    #           query+="""(employee in (SELECT name from tabEmployee where tabEmployee.sub_department in (select name from `tabDepartment` where manager='{0}')) ) or employee = '{0}'""".format( employee.name)
    #           # frappe.msgprint("hh")


    #       if u'HR Manager' in frappe.get_roles(user):
    #           # if query != "":
    #           #   query+=" or "
    #           # query+="""workflow_state='Approved By HR Specialist' or workflow_state='Created By CEO'  or (workflow_state='Approved By CEO' and total_leave_days >=5) or ((leave_type='Without Pay - غير مدفوعة' or leave_type='Annual Leave - اجازة اعتيادية' or leave_type='emergency -اضطرارية')and workflow_state='Approved By Director') or employee = '{0}'""".format(employee.name)
    #           return ""

    #       if u'HR Specialist' in frappe.get_roles(user):
    #           return ""

    #       if u'Employee' in frappe.get_roles(user):
    #           if query != "":
    #               query+=" or "
    #           query+=""" employee = '{0}'""".format(employee.name)
    #       # frappe.msgprint(query)
    #       return query
