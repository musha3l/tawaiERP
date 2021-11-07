# -*- coding: utf-8 -*-
# Copyright (c) 2015, Erpdeveloper.team and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe.utils import flt, getdate
from frappe.utils import cint
from frappe import _
from frappe.utils import nowdate, add_days
import frappe.desk.form.assign_to

import barcode
from barcode.writer import ImageWriter
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from umalqurra.hijri_date import HijriDate


class AdministrativeDecision(Document):

    def autoname(self):
        # if self.type == "Coming" :
        #   self.naming_series = "AD-IN/"
        # elif self.type == "Out" :
        #   self.naming_series = "AD-OUT/"
        # elif self.type == "Inside" :
        #   self.naming_series = "AD-INSIDE/"
        # else:
        #   self.naming_series = "AD/"

        naming_method = frappe.db.get_value("HR Settings", None, "emp_created_by")
        if not naming_method:
            throw(_("Please setup Employee Naming System in Human Resource > HR Settings"))
        else:
            if naming_method == 'Naming Series':
                self.name = make_autoname(self.naming_series + '.####')
        # self.transaction_number = self.name
        #
        # if self.type == "Sent Document" :
        #     self.issued_number = self.name


    def get_hijry(self):

        creation_date = datetime.datetime.strptime(self.creation_date, "%Y-%m-%d")
        um = HijriDate(creation_date.year,creation_date.month,creation_date.day,gr=True)
        # hijri_date = str('هـ'+str(int(um.year))+str(um.month) + str(int(um.day)))
        hijri_date = str(str(int(um.year)) + '-'+ str(int(um.month)) + '-' + str(int(um.day)))
        self.hijri_date = hijri_date
        # return str('هـ'+str(int(um.year))+str(um.month_name) + str(int(um.day)))




    # API for Generate Barcode Button
    # js calls api and give it name of image
    def barcode_attach2(self,name):
        try:
            # frappe.throw(str(name))
            barcode_class = barcode.get_barcode_class('code39')
            ean = barcode_class(name, ImageWriter(), add_checksum=False)
            barcode_path = frappe.get_site_path()+'/public/files/'
            ean.save(barcode_path+name)
            # ean.save(barcode_path+self.name+'.png')

            self.save_image("/files/", name + '.png')

            img_path = "/files/" + name + ".png"

            # frappe.db.sql("""update `tabAdministrative Decision` set barcode_img = %s
            #     where name = %s""", (img_path, name))
            # frappe.db.commit()

            self.barcode_img = img_path
            # administrative_doc = frappe.get_doc('Administrative Decision', name)
            # administrative_doc.barcode_img = img_path
            # administrative_doc.save()
            # frappe.db.commit()


            return img_path

        except Exception as e:
            raise e


    def barcode_attach(self):
        barcode_class = barcode.get_barcode_class('code39')
        ean = barcode_class(self.title, ImageWriter(), add_checksum=False)
        barcode_path = frappe.get_site_path()+'/public/files/'

        ean.save(barcode_path+self.title)
        # ean.save(barcode_path+self.name+'.png')

        self.save_image("/files/",self.title + '.png')

    def save_image(self,path, name):
        # save barcode image to file table
        attach_image = frappe.get_doc({
            "doctype": "File",
            "file_name": name,
            "file_url": path + name,
            "folder":"home"
        })

        attach_image.insert()

    def after_insert(self):
        pass
        # self.barcode_attach()
        # img_path = "/files/" + self.name + ".png"

        # frappe.db.sql("""update `tabAdministrative Decision` set barcode_img = %s
        #     where name = %s""", (img_path, self.name))
        # frappe.db.commit()

        # self.barcode_img = img_path
        # administrative_doc = frappe.get_doc('Administrative Decision', self.name)
        # administrative_doc.barcode_img = img_path
        # administrative_doc.save()
        # frappe.db.commit()



    def validate(self):
        # self.validate_dates()
        self.check_employee()
        self.validate_emp()

        # self.check_branch_department()
        # self.validate_fields()
        if self.get('docstatus') == 1:
            self.validate_approve()
            self.title = self.get_title_name()
            self.transaction_number = self.title
            self.issued_number = self.title
        #
            self.barcode_attach()
            img_path = "/files/" + self.title + ".png"
            self.barcode_img = img_path
            # if self.state != "Active" and  not self.get('__islocal'):
            #   frappe.throw(_("All board must Approve before submitted"))
        self.make_attachments_rqd_message()
        self.get_hijry()
        # if self.get("__islocal") :
        #     self.title = self.get_title_name()
        if self.get("__islocal") and self.type == 'Received Document':
            self.workflow_state = 'Created By GOV. AFFAIRS REPRESENTATIVE'
        if self.type == 'Sent Document' and self.workflow_state == 'Approved By Director':
            self.workflow_state = 'Approved By Director (AD.OUT)'
        if self.type == 'Sent Document' and self.workflow_state == 'Submitted(Director)':
            self.workflow_state = 'Submitted by Director (AD.OUT)'
        # if self.type == 'Sent Document' and self.workflow_state == 'Approved By The Signatory' or self.type == 'Inside Document' and self.workflow_state == 'Approved By The Signatory (INSIDE)':
        #     self.check_employee_approval()
        # if ((self.workflow_state == 'Approved by GOV. AFFAIRS REPRESENTATIVE') or (self.type == 'Inside Document' and self.workflow_state == 'Approved By The Signatory (INSIDE)')) :
            # self.check_employee_approval()
            # self.docstatus =1
            # self.validate_approve()
            # self.title = self.get_title_name()
            # self.transaction_number = self.title
            # self.issued_number = self.title
            #
            # self.barcode_attach()
            # img_path = "/files/" + self.title + ".png"
            # self.barcode_img = img_path
            # if self.state != "Active" and  not self.get('__islocal') and len(self.administrative_board) > 0:
            #     frappe.throw(_("All board must Approve before submitted"))




    def on_submit(self):
        self.validate_approve()
        if self.type == 'Inside Document':
            self.check_employee_approval()

        self.title = self.get_title_name()
        self.transaction_number = self.title
        self.issued_number = self.title

        # self.barcode_attach()
        # img_path = "/files/" + self.title + ".png"
        # self.barcode_img = img_path

        if self.state != "Active" and  not self.get('__islocal') and len(self.administrative_board) > 0:
            frappe.throw(_("All board must Approve before submitted"))


    def on_update(self):
        self.assign_to_admins()

    def assign_to_admins(self):
        pass

    def make_attachments_rqd_message(self):
        if not self.get('__islocal') and self.type == 'Received Document' and not (self.attach):
            frappe.throw(_("Please attach your files and then submit the form"))

    # def validate_dates(self):
    #   if getdate(self.start_date) > getdate(self.end_date):
    #       frappe.throw(_("End Date can not be less than Start Date"))

    def check_employee_approval(self):
        if self.type == 'Inside Document':
            issued_by = frappe.get_value("Employee", filters={"name": self.issued_by}, fieldname="user_id")

            # if self.issued_by_approval == '3':
            if not self.issued_by == 'EMP/2006':
                if issued_by != frappe.session.user:
                    frappe.throw("Current Letter need an approval from Employee {0}".format(self.issued_by_name))
            else:
                if 'ai.alamri@tawari.sa' != frappe.session.user:
                    frappe.throw("Current Letter need an approval from Employee احمد ابراهيم العمري")
            # self.issued_by_approval = self.issued_by_approval + 1

    def check_employee(self) :
        if self.type == "Inside Document" :
            if not self.employee:
                frappe.throw(_("Employee Missing"))
        elif self.type == "Received Document":
            if not self.coming_from:
                frappe.throw(_("The Issued Address Missing"))



    # def check_branch_department(self):
    #   if self.type == "Inside" :
    #       if not self.department or not self.branch:
    #           frappe.throw(_("Add Branch and Department information"))
    #       if not self.start_date:
    #           frappe.throw(_("Add Start Date"))

    # def validate_fields(self):
    #   if self.type == "Out":
    #       if not self.start_date:
    #           frappe.throw(_("Add Start Date"))
        # if self.type == "Out" or self.type == "Coming" :
        #   if not self.end_date:
        #       frappe.throw(_("Add End Date"))

    def get_title_name(self):
        from frappe.utils import getdate

        namming =frappe.get_list("Enhanced Nameing Doc", fields=["name","name_of_doc", "index_value","year"],filters={"year": str(getdate(self.creation_date).year),"name_of_doc":self.doctype},ignore_permissions=True)
        if namming :
			#~ title =self.name[:len(self.naming_series)] + str(getdate(self.posting_date).year) +"-"+ self.name[len(self.naming_series):]
            title =self.name[:len(self.naming_series)] + str(getdate(self.creation_date).year) +"-"+ str(namming[0]["index_value"]+1).zfill(5)
            nammeing_doc = frappe.get_doc("Enhanced Nameing Doc",namming[0]["name"])
            nammeing_doc.flags.ignore_permissions = True
            nammeing_doc.index_value = nammeing_doc.index_value+1
            nammeing_doc.save()
            return title
        else :
            title =self.name[:len(self.naming_series)] + str(getdate(self.creation_date).year) +"-"+ str(1).zfill(5)
            nammeing_doc = frappe.new_doc("Enhanced Nameing Doc")
            nammeing_doc.flags.ignore_permissions = True
            nammeing_doc.parent = "Enhanced Nameing"
            nammeing_doc.parenttype = "Enhanced Nameing"
            nammeing_doc.parentfield='enhanced_nameing'
            nammeing_doc.index_value = 1
            nammeing_doc.year = str(getdate(self.creation_date).year)
            nammeing_doc.name_of_doc = self.doctype
            nammeing_doc.save()
            return title

    def validate_approve(self):
        checker = 1
        decision = self.administrative_board
        if decision:
            for d in self.administrative_board :
                if d.decision != "Approve":
                    checker =0
            if checker==1:
                self.state = "Active"

    def unallowed_actions(self):
        if hasattr(self,"workflow_state"):
            permitted_departments = frappe.db.sql_list("select for_value from `tabUser Permission` where allow = 'Department' and user = '{0}'".format(frappe.session.user))
            if self.department not in permitted_departments and 'Manager' in frappe.get_roles(frappe.session.user) and self.workflow_state == "Submitted(Employee)":
                return True
            elif self.department not in permitted_departments and 'Director' in frappe.get_roles(frappe.session.user) and (self.workflow_state == "Submitted(Manager)" or self.workflow_state == "Approved by Manager" ):
                return True


    def change_administrative_board_decision(self,decision):
        administrative_board = frappe.get_doc('Administrative Board',{'parent' :self.name ,
        'user_id':frappe.session.user } )       # self.administrative_board
        if administrative_board :
            administrative_board.set("decision",decision)
            administrative_board.save()
        return administrative_board

    def validate_emp(self):
        if self.employee:
            employee_user = frappe.get_value("Employee", filters = {"name": self.employee}, fieldname="user_id")
            if self.get('__islocal') and employee_user:
                if (u'Director' in frappe.get_roles(employee_user)) and (self.type == "Inside Document" or self.type == "Sent Document"):
                    self.workflow_state = "Created By Director"
                if (u'Manager' in frappe.get_roles(employee_user)) and (self.type == "Inside Document" or self.type == "Sent Document"):
                    self.workflow_state = "Created By Manager"


def get_emp(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(""" select name,employee_name from `tabEmployee` """)


def get_emp_sign(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(""" select name,employee_name from `tabEmployee` where name = 'EMP/1002' or name = 'EMP/1004' or name = 'EMP/1008' or name = 'EMP/2006' """)


def get_permission_query_conditions(user):

    if 'GOV. AFFAIRS REPRESENTATIVE' in frappe.get_roles(frappe.session.user) or 'Purchase Master Manager'  in frappe.get_roles(frappe.session.user) or 'Director' in frappe.get_roles(frappe.session.user) :
        return  """(True)""";
    elif 'Manager' in frappe.get_roles(frappe.session.user):
        return  """(`tabAdministrative Decision`.owner ='{0}' or `tabAdministrative Decision`.priority ='Medium' or `tabAdministrative Decision`.priority ='Low' )""".format(frappe.session.user);
    else:
        return  """(`tabAdministrative Decision`.owner ='{0}' or `tabAdministrative Decision`.priority ="Low")""".format(frappe.session.user);


def has_permission(doc):
    if 'GOV. AFFAIRS REPRESENTATIVE' in frappe.get_roles(frappe.session.user) or 'Purchase Master Manager'  in frappe.get_roles(frappe.session.user) or 'Director' in frappe.get_roles(frappe.session.user):
        return True
    elif 'Manager' in frappe.get_roles(frappe.session.user):
        if not (doc.priority =="Low" or doc.priority == "Medium" or doc.owner == frappe.session.user) :
            return False
    else:
        if 'Employee' in frappe.get_roles(frappe.session.user):
            if not (doc.priority =="Low" or doc.owner == frappe.session.user):
                return False
