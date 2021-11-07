# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from math import ceil

class PromotionandMerit(Document):
    def on_submit(self):
        for promotion in self.promotion_and_merit_employee:
            if promotion.new_total_package > promotion.current_total_package:

                salary_structure = frappe.get_value("Salary Structure Employee", {"employee": promotion.employee}, "parent")
                if salary_structure:
                    str_doc = frappe.get_doc("Salary Structure", salary_structure)

                    emp_doc = frappe.get_doc("Employee", promotion.employee)
                    emp_doc.grade = promotion.new_grade
                    emp_doc.level = promotion.new_level
                    emp_doc.lvalue = promotion.new_base/100
                    emp_doc.save(ignore_permissions = True)

                    for i in str_doc.employees:
                        if i.employee==promotion.employee:
                            i.grade = promotion.new_grade
                            i.level = promotion.new_level
                            i.level_value = promotion.new_base/100
                            i.base = promotion.new_total_package
                    
                    str_doc.save(ignore_permissions = True)

                    msg = """Promotion is done for employee <b><a href="#Form/Employee/{emp}">{emp}</a></b>, salary structure number <b><a href="#Form/Salary Structure/{structure}">{structure}</a></b> has been edited""".format(emp=promotion.employee,structure=salary_structure)
                    frappe.msgprint(msg)         
        


    def after_insert(self):
        employees = frappe.db.sql("select emp.name,emp.employee_name,emp.grade,emp.level,grade.base from `tabEmployee` as emp join `tabGrade` as grade on emp.grade=grade.name where emp.status='Active' and emp.name like '%EMP/1%' and emp.name!='EMP/1012' ")
        for employee in employees:

            salary = employee[4]
            for l in range(1, employee[3]):
                salary += (salary*0.01)
                
            current_total_package = ceil(salary)
            self.append('promotion_and_merit_employee', {"employee": employee[0],"employee_name": employee[1],"current_grade": employee[2],"current_level": employee[3],"current_base": employee[4],"current_total_package": current_total_package})

    def validate_level_increase_value(self):
        frappe.msgprint("Increased Level cannot be more than 100!")

    def get_new_grade_level(self,current_level,current_grade,current_base,total_level):
        grade_list=[]
        next_grade=current_grade
        next_level=current_level
        next_base=current_base

        grades = frappe.db.sql("select name,base from `tabGrade` order by base")
        for grade in grades:
            grade_list.append(grade[0])

        if current_grade=="Grade C":
            frappe.throw("This Employee reach final Grade!")

        for emp_grade in range(len(grade_list)):
            if current_grade==grade_list[emp_grade]:
                next_grade = str(grade_list[emp_grade+1])

        get_new_base = frappe.db.sql("select base from `tabGrade` where name='{0}'".format(next_grade))
        if get_new_base:
            next_base = get_new_base[0][0]

        if total_level>=100:
            next_level=int(total_level)-100

        return next_grade,next_level,next_base

