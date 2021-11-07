# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import flt, getdate

from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from frappe.utils import date_diff, add_months, today, getdate, add_days, flt
from erpnext.hr.utils import set_employee_name

class Appraisal(Document):
    def validate(self):
        if not self.status:
            self.status = "Draft"
        if hasattr(self,"workflow_state"):
            if self.workflow_state:
                if "Rejected" in self.workflow_state:
                    self.docstatus = 1
                    self.docstatus = 2

        set_employee_name(self)
        self.validate_dates()
        self.validate_existing_appraisal()
        self.calculate_total()
        self.validate_emp()

        self.check_employee_approval()



    # def validate_emp(self):
    #     if self.get('__islocal'):
    #         if u'CEO' in frappe.get_roles(frappe.session.user):
    #             self.workflow_state = "Created By CEO"
    #         elif u'Director' in frappe.get_roles(frappe.session.user):
    #             self.workflow_state = "Created By Director"
    #         elif u'Manager' in frappe.get_roles(frappe.session.user):
    #             self.workflow_state = "Created By Manager"
    #         elif u'Line Manager' in frappe.get_roles(frappe.session.user):
    #             self.workflow_state = "Created By Line Manager"


    def validate_emp(self):
        if self.employee:
            employee_user = frappe.get_value("Employee", filters={"name": self.employee}, fieldname="user_id")
            # frappe.msgprint(str(employee_user))
            # frappe.msgprint(str(frappe.session.user))

            if self.get('__islocal') and employee_user:
                if u'Director' in frappe.get_roles(employee_user) and u'CEO' in frappe.get_roles(frappe.session.user):
                    self.workflow_state = "Created By CEO"
                elif u'Manager' in frappe.get_roles(employee_user) and u'Director' in frappe.get_roles(frappe.session.user):
                    self.workflow_state = "Created By Director"
                elif u'Line Manager' in frappe.get_roles(employee_user) and u'Manager' in frappe.get_roles(frappe.session.user):
                    self.workflow_state = "Created By Manager"
                elif u'Employee' in frappe.get_roles(employee_user) and u'Line Manager' in frappe.get_roles(frappe.session.user):
                    self.workflow_state = "Created By Line Manager"

            if not employee_user and self.get('__islocal'):
                self.workflow_state = "Created By Line Manager"

    def check_employee_approval(self):
        employee_user = frappe.get_value("Employee", filters={"name": self.employee}, fieldname="user_id")

        if self.employee_approval == 1:
            if employee_user != frappe.session.user:
                frappe.throw("Current Appraisal need an approval from employee {0}".format(self.employee_name))
        self.employee_approval=self.employee_approval+1

    def unallowed_actions(self):
        if self.workflow_state == "Created By CEO" or self.workflow_state == "Created By Director" or self.workflow_state == "Created By Manager" or self.workflow_state == "Created By Line Manager":
            employee_user = frappe.get_value("Employee", filters = {"name": self.employee}, fieldname="user_id")
            if employee_user != frappe.session.user:
                return True

    def get_employee_name(self):
        self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
        return self.employee_name

    def validate_dates(self):
        if getdate(self.start_date) > getdate(self.end_date):
            frappe.throw(_("End Date can not be less than Start Date"))

    def validate_existing_appraisal(self):
        chk = frappe.db.sql("""select name from `tabAppraisal` where employee=%s
            and (status='Submitted' or status='Completed')
            and ((start_date>=%s and start_date<=%s)
            or (end_date>=%s and end_date<=%s))""",
            (self.employee,self.start_date,self.end_date,self.start_date,self.end_date))
        if chk:
            frappe.throw(_("Appraisal {0} created for Employee {1} in the given date range").format(chk[0][0], self.employee_name))

    def calculate_total(self):
        total, total_w  = 0, 0
        for d in self.get('goals'):
            if d.score:
                d.score_earned = flt(d.score)
                # d.score_earned = flt(d.score) * flt(d.per_weightage) * 2 / 100
                total = total + d.score_earned
            total_w += flt(d.per_weightage)

        for d in self.get('quality_of_work_goals'):
            if d.score:
                d.score_earned = flt(d.score)
                # d.score_earned = flt(d.score) * flt(d.per_weightage) * 2 / 100
                total = total + d.score_earned
            total_w += flt(d.per_weightage)

        for d in self.get('work_habits_goals'):
            if d.score:
                d.score_earned = flt(d.score)
                # d.score_earned = flt(d.score) * flt(d.per_weightage) * 2 / 100
                total = total + d.score_earned
            total_w += flt(d.per_weightage)

        for d in self.get('job_knowledge_goals'):
            if d.score:
                d.score_earned = flt(d.score)
                # d.score_earned = flt(d.score) * flt(d.per_weightage) * 2 / 100
                total = total + d.score_earned
            total_w += flt(d.per_weightage)

        for d in self.get('interpersonal_relations_goals'):
            if d.score:
                d.score_earned = flt(d.score)
                # d.score_earned = flt(d.score) * flt(d.per_weightage) * 2 / 100
                total = total + d.score_earned
            total_w += flt(d.per_weightage)

        for d in self.get('leadership_goals'):
            if d.score:
                d.score_earned = flt(d.score)
                # d.score_earned = flt(d.score) * flt(d.per_weightage) * 2 / 100
                total = total + d.score_earned
            total_w += flt(d.per_weightage)

        if int(total_w) != 100:
            frappe.throw(_("Total weightage assigned should be 100%. It is {0}").format(str(total_w) + "%"))

        if frappe.db.get_value("Employee", self.employee, "user_id") != \
                frappe.session.user and total == 0:
            frappe.throw(_("Total cannot be zero"))

        self.total_score = total


        if self.total_score >= 95 and self.total_score <= 100 :
            self.attribute = "Outstanding"
        elif self.total_score >= 90 and self.total_score <= 94 :
            self.attribute = "Exceeds Requirements"
        elif self.total_score >= 80 and self.total_score <= 89 :
            self.attribute = "Meets Requirements"
        elif self.total_score >= 70 and self.total_score <= 79 :
            self.attribute = "Need Improvement"
        elif self.total_score >= 0 and self.total_score <= 69 :
            self.attribute = "Unsatisfactory"


    def on_submit(self):
        frappe.db.set(self, 'status', 'Submitted')
        employee = frappe.get_doc('Employee',{'name' : self.employee})
        appraisal = frappe.new_doc(u'Employee Performance History',employee,u'employee_performance_history')
        appraisal.update(
            {
                "appraisal_template": self.kra_template,
                "period":  self.period,
                "total_score":self.total_score,
                "attribute": self.attribute,
            })
        appraisal.insert()

    def on_cancel(self):
        frappe.db.set(self, 'status', 'Cancelled')

@frappe.whitelist()
def fetch_appraisal_template(source_name, target_doc=None):
    target_doc = get_mapped_doc("Appraisal Template", source_name, {
        "Appraisal Template": {
            "doctype": "Appraisal",
        },
        "Appraisal Template Goal": {
            "doctype": "Appraisal Goal",
        }
    }, target_doc)


    target_doc = get_mapped_doc("Appraisal Template", source_name, {
        "Appraisal Template": {
            "doctype": "Appraisal",
        },
        "Appraisal Template Goal Quality of Work": {
            "doctype": "Appraisal Goal Quality of Work",
        }
    }, target_doc)


    target_doc = get_mapped_doc("Appraisal Template", source_name, {
        "Appraisal Template": {
            "doctype": "Appraisal",
        },
        "Appraisal Template Goal Work Habits": {
            "doctype": "Appraisal Goal Work Habits",
        }
    }, target_doc)


    target_doc = get_mapped_doc("Appraisal Template", source_name, {
        "Appraisal Template": {
            "doctype": "Appraisal",
        },
        "Appraisal Template Goal Job Knowledge": {
            "doctype": "Appraisal Goal Job Knowledge",
        }
    }, target_doc)


    target_doc = get_mapped_doc("Appraisal Template", source_name, {
        "Appraisal Template": {
            "doctype": "Appraisal",
        },
        "Appraisal Template Goal Interpersonal relations": {
            "doctype": "Appraisal Goal Interpersonal relations",
        }
    }, target_doc)


    target_doc = get_mapped_doc("Appraisal Template", source_name, {
        "Appraisal Template": {
            "doctype": "Appraisal",
        },
        "Appraisal Template Goal Leadership": {
            "doctype": "Appraisal Goal Leadership",
        }
    }, target_doc)

    return target_doc

def appraisal_creation_and_contacting_manager():
    pass
    # from frappe.utils.data import flt, nowdate, getdate, cint
    # import datetime
    # from datetime import date
    # from dateutil.relativedelta import relativedelta
    #
    # length=frappe.db.sql("select count(name) from `tabEmployee` where status!='left'")
    # emp=frappe.db.sql("select name,employee_name,department,date_of_joining,reports_to,employee_name_english from `tabEmployee` where status!='left'")
    # for i in range(length[0][0]):
    #     # date_of_joining = datetime.datetime.strptime(str(emp[i][3]), '%Y-%m-%d')
    #     # next_two_monthes = date(date_of_joining.year, date_of_joining.month, date_of_joining.day) + relativedelta(months=+2)
    #
    #     nowdate = frappe.utils.nowdate()
    #
    #     next_two_monthes = frappe.utils.add_months(getdate(emp[i][3]), +2)
    #
    #     print emp[i][0],emp[i][3],next_two_monthes
    #
    #     # if getdate(nowdate) == getdate(next_two_monthes):
    #     if emp[i][0]=='EMP/1024':
    #         if (emp[i][5]):
    #             emp_name = emp[i][5]
    #         else:
    #             emp_name = emp[i][1]
    #         print('****************')
    #         print(emp_name)
    #         print(emp[i][0])
    #         print(emp[i][3])
    #         print(next_two_monthes)
    #         first_manager_email=None
    #         second_manager_email=None
    #         workflow_state = "Created By Line Manager"
    #         first_manager = frappe.db.sql("""select line_manager,manager,director,parent_department from `tabDepartment` where name="{0}" """.format(emp[i][2]),as_dict=True)
    #         if(first_manager):
    #             second_manager = frappe.db.sql("""select line_manager,manager,director,parent_department from `tabDepartment` where name="{0}" """.format(first_manager[0].parent_department),as_dict=True)
    #             if(first_manager[0].line_manager):
    #                 first_manager_email = frappe.db.sql("""select prefered_email from `tabEmployee` where name="{0}" """.format(str(first_manager[0].line_manager)))
    #             elif(first_manager[0].manager):
    #                 first_manager_email = frappe.db.sql("""select prefered_email from `tabEmployee` where name="{0}" """.format(str(first_manager[0].manager)))
    #                 workflow_state = "Created By Line Manager"
    #             elif(first_manager[0].director):
    #                 first_manager_email = frappe.db.sql("""select prefered_email from `tabEmployee` where name="{0}" """.format(str(first_manager[0].director)))
    #                 workflow_state = "Created By Manager"
    #             if(second_manager):
    #                 if(second_manager[0].line_manager):
    #                     second_manager_email = frappe.db.sql("""select prefered_email from `tabEmployee` where name="{0}" """.format(str(second_manager[0].line_manager)))
    #                 elif(second_manager[0].manager):
    #                     second_manager_email = frappe.db.sql("""select prefered_email from `tabEmployee` where name="{0}" """.format(str(second_manager[0].manager)))
    #                 elif(second_manager[0].director):
    #                     second_manager_email = frappe.db.sql("""select prefered_email from `tabEmployee` where name="{0}" """.format(str(second_manager[0].director)))
    #         recipients = ""
    #         if(first_manager_email):
    #             if(first_manager_email[0][0]):
    #                 first_manager_email = first_manager_email[0][0]
    #                 recipients +=(first_manager_email) + ", "
    #         if(second_manager_email):
    #             if(second_manager_email[0][0]):
    #                 second_manager_email = second_manager_email[0][0]
    #                 recipients+=(second_manager_email) + ", "
    #         recipients1 = first_manager_email
    #         recipients2 = second_manager_email
    #
    #         print '****************************'
    #         print recipients1
    #         print recipients2
    #         print '****************************'
    #
    #         appraisal = frappe.get_doc({
    #             "doctype": "Appraisal",
    #             "employee": emp[i][0],
    #             "employee_name":emp[i][1],
    #             "period": "2018 - 2",
    #             "workflow_state":workflow_state,
    #             "department":emp[i][2]
    #             })
    #         appraisal.flags.ignore_validate = True
    #         appraisal.flags.ignore_mandatory = True
    #         appraisal.save()
    #         frappe.db.commit()
    #         content_msg= "<html><H4>Employee {0} has been here for two monthes, Appraisal Form is created </H4><p> Please follow up at Link: <a href='http://95.85.8.23:8000/desk#Form/Appraisal/{1}'+> {1}</a> </p> </html>".format(emp_name,appraisal.name)
    #         from frappe.core.doctype.communication.email import make
    #         try:
    #             frappe.flags.sent_mail = None
    #             if recipients1:
    #                 make(subject = "Appraisal Notification For Employee: {0}".format(emp_name) , content=content_msg, recipients=recipients1,
    #                     send_email=True, sender="erp@tawari.sa")
    #             if recipients2:
    #                 make(subject = "Appraisal Notification For Employee: {0}".format(emp_name) , content=content_msg, recipients=recipients2,
    #                     send_email=True, sender="erp@tawari.sa")
    #             # break
    #         except:
    #             frappe.msgprint("appraisal_creation_and_contacting_manager"+ " method is broken")
