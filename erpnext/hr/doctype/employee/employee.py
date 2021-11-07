# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import getdate, validate_email_add, today, add_years ,date_diff,nowdate
from frappe.model.naming import make_autoname
from frappe import throw, _
import frappe.permissions
from frappe.model.document import Document
from erpnext.utilities.transaction_base import delete_events


class EmployeeUserDisabledError(frappe.ValidationError):
    pass


class Employee(Document):
    def autoname(self):
        naming_method = frappe.db.get_value("HR Settings", None, "emp_created_by")
        if not naming_method:
            throw(_("Please setup Employee Naming System in Human Resource > HR Settings"))
        else:
            if naming_method == 'Naming Series':
                self.name = make_autoname(self.naming_series + '.###')
            elif naming_method == 'Employee Number':
                self.name = self.employee_number

        self.employee = self.name

    def validate(self):
        from erpnext.controllers.status_updater import validate_status
        validate_status(self.status, ["Active", "Left"])

        self.employee = self.name
        self.validate_date()
        self.validate_email()
        self.validate_status()
        self.validate_employee_leave_approver()
        self.validate_reports_to()

        if self.user_id:
            self.validate_for_enabled_user_id()
            self.validate_duplicate_user_id()
        else:
            existing_user_id = frappe.db.get_value("Employee", self.name, "user_id")
            if existing_user_id:
                frappe.permissions.remove_user_permission(
                    "Employee", self.name, existing_user_id)
        self.validate_employee_custody()
        self.validate_exp_dates()
    def validate_exp_dates(self):

        from frappe.utils import getdate, add_months, nowdate
        message_hold = ""
        self.is_message = 0
        if self.contract_end_date:
            if getdate(self.contract_end_date) <= getdate(add_months(nowdate(), 3)):
                message_hold += "<h5>The contract end date will be on {0}</h5><br />".format(self.contract_end_date)
                self.is_message = 1

        if self.civil_id_expiry_date:
            if getdate(self.civil_id_expiry_date) <= getdate(add_months(nowdate(), 2)):
                message_hold += "<h5>The civil ID expiry date will be on {0}</h5><br />".format(self.civil_id_expiry_date)
                self.is_message = 1

        if self.driving_licence_expiry_date:
            if getdate(self.driving_licence_expiry_date) <= getdate(add_months(nowdate(), 2)):
                message_hold += "<h5>The driving licence expiry date will be on {0}</h5><br />".format(self.driving_licence_expiry_date)
                self.is_message = 1

        self.message = message_hold

    def validate_employee_custody(self):
        if self.status == 'Left':
            ac = frappe.db.get_values("Fixed Asset Custody", {"employee": self.employee,
            "docstatus": 1}, ["fixed_asset", "item_code"], as_dict=True)
            if ac:
                frappe.throw(_("This employee has custody {0} and should be cancelled in the Fixed Asset Custody before marked as Left".format(ac[0])))

    def on_update(self):
        if self.user_id:
            self.update_user()
            self.update_user_permissions()

    def update_user_permissions(self):
        frappe.permissions.add_user_permission("Employee", self.name, self.user_id)
        frappe.permissions.set_user_permission_if_allowed("Company", self.company, self.user_id)

    def update_user(self):
        # add employee role if missing
        user = frappe.get_doc("User", self.user_id)
        user.flags.ignore_permissions = True

        if "Employee" not in user.get("roles"):
            user.add_roles("Employee")

        # copy details like Fullname, DOB and Image to User
        if self.employee_name and not (user.first_name and user.last_name):
            employee_name = self.employee_name.split(" ")
            if len(employee_name) >= 3:
                user.last_name = " ".join(employee_name[2:])
                user.middle_name = employee_name[1]
            elif len(employee_name) == 2:
                user.last_name = employee_name[1]

            user.first_name = employee_name[0]

        if self.date_of_birth:
            user.birth_date = self.date_of_birth

        if self.gender:
            user.gender = self.gender

        if self.image:
            if not user.user_image:
                user.user_image = self.image
                try:
                    frappe.get_doc({
                        "doctype": "File",
                        "file_name": self.image,
                        "attached_to_doctype": "User",
                        "attached_to_name": self.user_id
                    }).insert()
                except frappe.DuplicateEntryError:
                    # already exists
                    pass

        user.save()

    def validate_date(self):
        if self.date_of_birth and getdate(self.date_of_birth) > getdate(today()):
            throw(_("Date of Birth cannot be greater than today."))

        if self.date_of_birth and self.date_of_joining and getdate(self.date_of_birth) >= getdate(self.date_of_joining):
            throw(_("Date of Joining must be greater than Date of Birth"))

        elif self.date_of_retirement and self.date_of_joining and (getdate(self.date_of_retirement) <= getdate(self.date_of_joining)):
            throw(_("Date Of Retirement must be greater than Date of Joining"))

        elif self.relieving_date and self.date_of_joining and (getdate(self.relieving_date) <= getdate(self.date_of_joining)):
            throw(_("Relieving Date must be greater than Date of Joining"))

        elif self.contract_end_date and self.date_of_joining and (getdate(self.contract_end_date) <= getdate(self.date_of_joining)):
            throw(_("Contract End Date must be greater than Date of Joining"))

    def validate_email(self):
        if self.company_email:
            validate_email_add(self.company_email, True)
        if self.personal_email:
            validate_email_add(self.personal_email, True)

    def validate_status(self):
        if self.status == 'Left' and not self.relieving_date:
            throw(_("Please enter relieving date."))

    def validate_for_enabled_user_id(self):
        if not self.status == 'Active':
            return
        enabled = frappe.db.get_value("User", self.user_id, "enabled")
        if enabled is None:
            frappe.throw(_("User {0} does not exist").format(self.user_id))
        if enabled == 0:
            frappe.throw(_("User {0} is disabled").format(self.user_id), EmployeeUserDisabledError)

    def validate_duplicate_user_id(self):
        employee = frappe.db.sql_list("""select name from `tabEmployee` where
            user_id=%s and status='Active' and name!=%s""", (self.user_id, self.name))
        if employee:
            throw(_("User {0} is already assigned to Employee {1}").format(
                self.user_id, employee[0]), frappe.DuplicateEntryError)

    def validate_employee_leave_approver(self):
        for l in self.get("leave_approvers")[:]:
            if "Leave Approver" not in frappe.get_roles(l.leave_approver):
                frappe.get_doc("User", l.leave_approver).add_roles("Leave Approver")

    def validate_reports_to(self):
        if self.reports_to == self.name:
            throw(_("Employee cannot report to himself."))

    def on_trash(self):
        delete_events(self.doctype, self.name)
    
    def update_level(self):
        from math import ceil
        salary_list = frappe.get_list("Salary Structure Employee", fields=["*"], filters={"employee":self.name})
        if salary_list : 
            for salary in salary_list:
                doc = frappe.get_doc("Salary Structure Employee",salary["name"])
                grade =frappe.get_doc("Grade",self.grade)
                level =int(self.level)
                salary = grade.base 
                percent = float(grade.level_percent)/100
                for l in range(1, level):
                    salary += salary *percent
                doc.base = ceil(salary)
                doc.grade = self.grade
                doc.level = self.level
                doc.save(ignore_permissions=True)
            return "Changed"
        else:
            return "No active salary structure"



def passport_validate_check():
    from frappe.core.doctype.communication.email import make
    frappe.flags.sent_mail = None

    emp = frappe.db.sql("select name,valid_upto,user_id,passport_validation_notification from `tabEmployee`")
    for i in emp:
        if i[1] and i[3]:
            date_difference = date_diff(i[1], getdate(nowdate()))

            if date_difference <= 14 :
                content_msg_emp="Your passport validity will end after {0} days".format(date_difference)
                content_msg_mng="Passport validity will end after {0} days for employee: {1}".format(date_difference,i[0])

                prefered_email = frappe.get_value("Employee", filters = {"user_id": i[2]}, fieldname = "prefered_email")
                prefered_email_mng = frappe.get_value("Employee", filters = {"user_id": 'am.aldahmash@tawari.sa'}, fieldname = "prefered_email")
                if prefered_email:
                    try:
                        sent = 0
                        make(subject = "Passport Validity Notification", content=content_msg_emp, recipients=prefered_email,
                            send_email=True, sender="erp@tawari.sa")

                        # make(subject = "Passport Validity Notification", content=content_msg_mng, recipients=prefered_email_mng,
                        #     send_email=True, sender="erp@tawari.sa")

                        sent = 1
                        print 'send email for '+prefered_email
                    except:
                        frappe.msgprint("could not send")

                print content_msg_emp
                print content_msg_mng
                print '----------------------------------------------------------------'
            else:
                pass




def get_timeline_data(doctype, name):
    '''Return timeline for attendance'''
    return dict(frappe.db.sql('''select unix_timestamp(attendance_date), count(*)
        from `tabAttendance` where employee=%s
            and attendance_date > date_sub(curdate(), interval 1 year)
            and status in ('Present', 'Half Day')
            group by attendance_date''', name))

@frappe.whitelist()
def get_retirement_date(date_of_birth=None):
    ret = {}
    if date_of_birth:
        try:
            retirement_age = int(frappe.db.get_single_value("HR Settings", "retirement_age") or 60)
            dt = add_years(getdate(date_of_birth),retirement_age)
            ret = {'date_of_retirement': dt.strftime('%Y-%m-%d')}
        except ValueError:
            # invalid date
            ret = {}

    return ret


def validate_employee_role(doc, method):
    # called via User hook
    if "Employee" in [d.role for d in doc.get("roles")]:
        if not frappe.db.get_value("Employee", {"user_id": doc.name}):
            frappe.msgprint(_("Please set User ID field in an Employee record to set Employee Role"))
            doc.get("roles").remove(doc.get("roles", {"role": "Employee"})[0])

def update_user_permissions(doc, method):
    # called via User hook
    if "Employee" in [d.role for d in doc.get("roles")]:
        employee = frappe.get_doc("Employee", {"user_id": doc.name})
        employee.update_user_permissions()

def send_birthday_reminders():
    """Send Employee birthday reminders if no 'Stop Birthday Reminders' is not set."""
    if int(frappe.db.get_single_value("HR Settings", "stop_birthday_reminders") or 0):
        return

    from frappe.utils.user import get_enabled_system_users
    users = None

    birthdays = get_employees_who_are_born_today()

    if birthdays:
        if not users:
            users = [u.email_id or u.name for u in get_enabled_system_users()]

        for e in birthdays:
            frappe.sendmail(recipients=filter(lambda u: u not in (e.company_email, e.personal_email, e.user_id), users),
                subject=_("Birthday Reminder for {0}").format(e.employee_name),
                message=_("""Today is {0}'s birthday!""").format(e.employee_name),
                reply_to=e.company_email or e.personal_email or e.user_id)

def get_employees_who_are_born_today():
    """Get Employee properties whose birthday is today."""
    return frappe.db.sql("""select name, personal_email, company_email, user_id, employee_name
        from tabEmployee where day(date_of_birth) = day(%(date)s)
        and month(date_of_birth) = month(%(date)s)
        and status = 'Active'""", {"date": today()}, as_dict=True)

def get_holiday_list_for_employee(employee, raise_exception=True):
    if employee:
        holiday_list, company = frappe.db.get_value("Employee", employee, ["holiday_list", "company"])
    else:
        holiday_list=''
        company=frappe.db.get_value("Global Defaults", None, "default_company")

    if not holiday_list:
        holiday_list = frappe.db.get_value("Company", company, "default_holiday_list")

    if not holiday_list and raise_exception:
        frappe.throw(_('Please set a default Holiday List for Employee {0} or Company {1}').format(employee, company))

    return holiday_list

def is_holiday(employee, date=None):
    '''Returns True if given Employee has an holiday on the given date

    :param employee: Employee `name`
    :param date: Date to check. Will check for today if None'''

    holiday_list = get_holiday_list_for_employee(employee)
    if not date:
        date = today()

    if holiday_list:
        return frappe.get_all('Holiday List', dict(name=holiday_list, holiday_date=date)) and True or False

@frappe.whitelist()
def deactivate_sales_person(status = None, employee = None):
    if status == "Left":
        sales_person = frappe.db.get_value("Sales Person", {"Employee": employee})
        if sales_person:
            frappe.db.set_value("Sales Person", sales_person, "enabled", 0)

def hooked_validate_exp_dates():

    from frappe.utils import getdate, add_months, nowdate
    emps = frappe.get_all("Employee")
    if emps:
        for emp in emps:
            emp_doc = frappe.get_doc("Employee", emp.name)
            message_hold = ""
            emp_doc.is_message = 0
            if emp_doc.contract_end_date:
                if getdate(emp_doc.contract_end_date) <= getdate(add_months(nowdate(), 3)):
                    message_hold += "<h5>The contract end date will be on {0}</h5><br />".format(emp_doc.contract_end_date)
                    emp_doc.is_message = 1

            if emp_doc.civil_id_expiry_date:
                if getdate(emp_doc.civil_id_expiry_date) <= getdate(add_months(nowdate(), 2)):
                    message_hold += "<h5>The civil ID expiry date will be on {0}</h5><br />".format(emp_doc.civil_id_expiry_date)
                    emp_doc.is_message = 1

            if emp_doc.driving_licence_expiry_date:
                if getdate(emp_doc.driving_licence_expiry_date) <= getdate(add_months(nowdate(), 2)):
                    message_hold += "<h5>The driving licence expiry date will be on {0}</h5><br />".format(emp_doc.driving_licence_expiry_date)
                    emp_doc.is_message = 1

            if emp_doc.message != message_hold:
                emp_doc.message = message_hold
                emp_doc.save(ignore_permissions=True)
                frappe.db.commit()


