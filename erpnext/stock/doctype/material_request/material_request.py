# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# ERPNext - web based ERP (http://erpnext.com)
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe

from frappe.utils import cstr, flt, getdate, new_line_sep
from frappe import msgprint, _
from frappe.model.mapper import get_mapped_doc
from erpnext.stock.stock_balance import update_bin_qty, get_indented_qty
from erpnext.controllers.buying_controller import BuyingController
from erpnext.manufacturing.doctype.production_order.production_order import get_item_details
from frappe import utils

form_grid_templates = {
    "items": "templates/form_grid/material_request_grid.html"
}

class MaterialRequest(BuyingController):
    def get_feed(self):
        return _("{0}: {1}").format(self.status, self.material_request_type)

    def check_if_already_pulled(self):
        pass

    def validate_qty_against_so(self):
        so_items = {} # Format --> {'SO/00001': {'Item/001': 120, 'Item/002': 24}}
        for d in self.get('items'):
            if d.sales_order:
                if not so_items.has_key(d.sales_order):
                    so_items[d.sales_order] = {d.item_code: flt(d.qty)}
                else:
                    if not so_items[d.sales_order].has_key(d.item_code):
                        so_items[d.sales_order][d.item_code] = flt(d.qty)
                    else:
                        so_items[d.sales_order][d.item_code] += flt(d.qty)

        for so_no in so_items.keys():
            for item in so_items[so_no].keys():
                already_indented = frappe.db.sql("""select sum(qty)
                    from `tabMaterial Request Item`
                    where item_code = %s and sales_order = %s and
                    docstatus = 1 and parent != %s""", (item, so_no, self.name))
                already_indented = already_indented and flt(already_indented[0][0]) or 0

                actual_so_qty = frappe.db.sql("""select sum(qty) from `tabSales Order Item`
                    where parent = %s and item_code = %s and docstatus = 1""", (so_no, item))
                actual_so_qty = actual_so_qty and flt(actual_so_qty[0][0]) or 0

                if actual_so_qty and (flt(so_items[so_no][item]) + already_indented > actual_so_qty):
                    frappe.throw(_("Material Request of maximum {0} can be made for Item {1} against Sales Order {2}").format(actual_so_qty - already_indented, item, so_no))

    def validate_schedule_date(self):
        for d in self.get('items'):
            if d.schedule_date and getdate(d.schedule_date) < getdate(self.transaction_date):
                frappe.throw(_("Expected Date cannot be before Material Request Date"))

    # Validate
    # ---------------------
    def validate(self):
        super(MaterialRequest, self).validate()

        # self.validate_schedule_date()
        self.validate_uom_is_integer("uom", "qty")

        if not self.status:
            self.status = "Draft"

        from erpnext.controllers.status_updater import validate_status
        validate_status(self.status, ["Draft", "Submitted", "Stopped", "Cancelled"])

        pc_obj = frappe.get_doc('Purchase Common')
        pc_obj.validate_for_items(self)
        self.validate_department()
        # self.validate_director()
        self.validate_emp_requester()
        # self.validate_project_manager()
        # self.validate_project()
        # self.validate_project_items()
        # self.set_title()


        if self.get("__islocal"):
            self.validate_director_role()
            self.title = self.get_title()
            self.set_user_emp()


    def validate_director_role(self):
        if "Director" in frappe.get_roles(frappe.session.user):
            self.workflow_state = 'Approved By Director'


    def validate_project_items(self):
        if self.project :
            warehouse = frappe.db.get_value("Project", self.project, "default_warehouse")
            if not warehouse :
                frappe.throw(_("Set Default Warehouse in Project %s"%self.project))
            else:
                self.default_warehouse = warehouse
                for row in self.get("items"):
                    if not row.warehouse :
                        row.warehouse = warehouse
                    elif row.warehouse !=warehouse :
                        frappe.throw(_("Bad Warehouse in row  %s default warehouse is %s"%(row.idx,warehouse)))



    def validate_suggested_price(self,item_name):
        resources_details_name = frappe.db.sql("select name from `tabItems Details` where parenttype='Project Initiation' and parent='{0}' and section_name='{1}' ".format(self.project,self.main_project_procurement))
        result = 0
        for resource in resources_details_name:
            doc = frappe.get_doc("Items Details",resource[0])
            if doc.items == item_name:
                result = doc.total_cost_price
        return result





    def get_title(self):
        from frappe.utils import getdate

        namming =frappe.get_list("Enhanced Nameing Doc", fields=["name","name_of_doc", "index_value","year"],filters={"year": str(getdate(self.posting_date).year),"name_of_doc":self.doctype,"naming_series":self.naming_series},ignore_permissions=True)
        if namming :
            #~ title =self.name[:len(self.naming_series)] + str(getdate(self.posting_date).year) +"-"+ self.name[len(self.naming_series):]
            title =self.name[:len(self.naming_series)] + str(getdate(self.posting_date).year) +"-"+ str(namming[0]["index_value"]+1).zfill(5)
            nammeing_doc = frappe.get_doc("Enhanced Nameing Doc",namming[0]["name"])
            nammeing_doc.flags.ignore_permissions = True
            nammeing_doc.index_value = nammeing_doc.index_value+1
            nammeing_doc.save()
            return title
        else :
            title =self.name[:len(self.naming_series)] + str(getdate(self.posting_date).year) +"-"+ str(1).zfill(5)
            nammeing_doc = frappe.new_doc("Enhanced Nameing Doc")
            nammeing_doc.flags.ignore_permissions = True
            nammeing_doc.parent = "Enhanced Nameing"
            nammeing_doc.parenttype = "Enhanced Nameing"
            nammeing_doc.index_value = 1
            nammeing_doc.year = str(getdate(self.posting_date).year)
            nammeing_doc.name_of_doc = self.doctype
            nammeing_doc.naming_series = self.naming_series
            nammeing_doc.save()
            return title


        # self.validate_qty_against_so()
        # NOTE: Since Item BOM and FG quantities are combined, using current data, it cannot be validated
        # Though the creation of Material Request from a Production Plan can be rethought to fix this
    def validate_emp_requester(self):
        if self.get('__islocal') or self.state == "Initiated":
            if self.material_requester:
                user = frappe.get_value("Employee", filters = {'name' : self.material_requester}, fieldname = "user_id")
                # if u'Project Manager' in frappe.get_roles(user) and self.purchase_workflow == "Project":
                #     self.workflow_state = "Created By Project Manager"
                # else:
                self.workflow_state = "Pending"

    def unallowed_actions(self):
        if self.state == "To Modify" or self.state == "Rejected":
            employee_user = frappe.get_value("Employee", filters = {"name": self.material_requester}, fieldname="user_id")
            if employee_user != frappe.session.user:
                return True

    def after_insert(self):
        self.validate_adding_mr()

    def set_user_emp(self):
        usr = frappe.get_value("Employee", filters = {"name": self.material_requester}, fieldname="user_id")
        if usr:
            self.set("user_id",usr)
    # def validate_wf_transition():

    #   if self.workflow_state:
    #       if self.workflow_state == "Pending" or self.workflow_state == "Modified":
    #           if u'Director' in frappe.get_roles(frappe.session.user):
    def validate_director_actions(self):
        if hasattr(self,'workflow_state'):
            if "Director" in frappe.get_roles(frappe.session.user) and not self.project:
                # frappe.msgprint(str(pu))

                department_info = frappe.db.sql("""select rgt,lft from `tabDepartment` where name ='{0}' """.format(self.department),as_dict=True)
                if department_info:
                    director_department = frappe.db.sql("""select name,director from `tabDepartment` where lft <= {lft} and rgt >= {rgt} and director is not null""".format(rgt=department_info[0].rgt,lft=department_info[0].lft),as_dict=True)
                    if director_department:
                        emp = frappe.get_doc("Employee",director_department[0].director)
                        if emp:
                            if emp.user_id == frappe.session.user:
                                return 'True'

        return 'False'


                # department = frappe.get_doc("Department",self.department)
                # while(department.parent_department != 'الادارة العليا'):
                #     if(department.director):
                #         director = frappe.get_doc("Employee",department.director)
                #         if(director.user_id == frappe.session.user):
                #             pu = frappe.get_value("User Permission", filters = {"allow": "Department", "for_value": self.department}, fieldname = "user")
                #             return 'True'
                #     department = frappe.get_doc("Department",department.parent_department)

                # return 'False'

                # if pu != frappe.session.user:
                #     return 'False'
                # else:
                #     return 'True'

        # if u'Director' in frappe.get_roles(frappe.session.user) and self.purchase_workflow != "Project" and self.workflow_state == "Approved By Project Budget Controller":
        #   if frappe.permissions.has_permission("Department", ptype='read', doc=self.department, verbose=False, user=frappe.session.user):
        #       self.workflow_state = "Approved By Director" if self.state == "Approved" else   "Rejected By Director"
    # def validate_project_manager(self):
    #         pms_str = self.get_project_manager()
    #         if pms_str:
    #             pms_list = pms_str.split(",")
    #             if self.material_requester not in pms_list:
    #                 frappe.throw(_("The selected Material Requester is not valid as a Project Manager"))


    # def get_project_manager(self):
    #     if self.project:
    #         pms = frappe.db.sql("""select name from tabEmployee where user_id in
    #             (select parent from `tabUserRole` where role = 'Project Manager')""", as_dict = True)
    #         if pms :
    #             pms_str = ""
    #             for pm in pms:
    #                 pms_str += pm.name+","
    #             pms_str = pms_str[:-1]
    #             return pms_str


    def get_project_items(self):
        resources_details_name = frappe.db.sql("select name from `tabItems Details` where parenttype='Project Initiation' and parent='{0}' and section_name='{1}' ".format(self.project,self.main_project_procurement))
        self.items = []
        for resource in resources_details_name:

            doc = frappe.get_doc("Items Details",resource[0])

            item = frappe.get_doc("Item", doc.items)
            description=item.description

            qty = 1
            if flt(doc.quantity)>0:
                qty = doc.quantity

            self.append("items", {
                "item_code": doc.items,
                "item_name": item.item_name,
                "description": description,
                "uom": "Nos",
                "qty": qty,
                "project": self.project,
                "schedule_date": frappe.utils.get_last_day(utils.today())
            })

            product_bundle = frappe.db.sql("""select t1.item_code, t1.qty, t1.uom, t1.description
                from `tabProduct Bundle Item` t1, `tabProduct Bundle` t2
                where t2.new_item_code=%s and t1.parent = t2.name order by t1.idx""", doc.items, as_dict=1)

            for bundle in product_bundle:
                item_bundle = frappe.get_doc("Item", bundle.item_code)

                self.append("items", {
                    "item_code": bundle.item_code,
                    "item_name": bundle.item_name,
                    "description": bundle.description,
                    "uom": bundle.uom,
                    "qty": flt(bundle.qty)*flt(qty),
                    "project": self.project,
                    "warehouse": item_bundle.default_warehouse,
                    "schedule_date": frappe.utils.get_last_day(utils.today()),
                    "is_product_bundle_item": 1 ,
                    "product_bundle": doc.items
                })


    def validate_project(self):
        if self.project:
            pro_list = frappe.get_list("Project", filters = {"project_manager": self.material_requester}, fields = ["name"])
            if not pro_list:
                frappe.throw(_("The Project is not valid"))
            else:
                for item in self.get("items"):
                    item.project = self.project

    def validate_adding_mr(self):
        if self.material_requester:
            user_emp = frappe.db.sql("select user_id from `tabEmployee` where name = '{0}'".format(self.material_requester), as_dict = 1)
            # frappe.throw(user_emp[0].user_id)
            frappe.get_doc(dict(
            doctype='User Permission',
            user=user_emp[0].user_id,
            allow="Material Request",
            for_value=self.name,
            apply_for_all_roles = False
            )).insert(ignore_permissions = True)
            # user = frappe.get_doc("User", user_emp[0].user_id)
            # frappe.permissions.add_user_permission("Material Request", self.name, user_emp[0].user_id, apply=False)
    def on_trash(self):
        user_emp = frappe.db.sql("select user_id from `tabEmployee` where name = '{0}'".format(self.material_requester), as_dict = 1)
        mr = frappe.get_value("User Permission", filters ={'user': user_emp[0].user_id, 'allow': 'Material Request', 'for_value': self.name}, fieldname = "name")
        if mr:
            frappe.delete_doc("User Permission", mr, ignore_permissions=True)

    def validate_department(self):
        if self.get("__islocal") :
            if self.purchase_workflow == "Project":
                self.department = None
            else:
                emp_dep = frappe.get_value("Employee", filters={"name": self.material_requester}, fieldname="department")
                if emp_dep:
                    self.department = emp_dep

    def set_title(self):
        '''Set title as comma separated list of items'''
        items = []
        for d in self.items:
            if d.item_code not in items:
                items.append(d.item_code)
            if(len(items)==4):
                break

        self.title = ', '.join(items)

    def on_submit(self):
        frappe.db.set(self, 'status', 'Submitted')
        self.update_requested_qty()

    def check_modified_date(self):
        mod_db = frappe.db.sql("""select modified from `tabMaterial Request` where name = %s""",
            self.name)
        date_diff = frappe.db.sql("""select TIMEDIFF('%s', '%s')"""
            % (mod_db[0][0], cstr(self.modified)))

        if date_diff and date_diff[0][0]:
            frappe.throw(_("{0} {1} has been modified. Please refresh.").format(_(self.doctype), self.name))

    def update_status(self, status):
        self.check_modified_date()
        frappe.db.set(self, 'status', cstr(status))
        self.update_requested_qty()

    def on_cancel(self):
        pc_obj = frappe.get_doc('Purchase Common')

        pc_obj.check_for_closed_status(self.doctype, self.name)

        self.update_requested_qty()

        frappe.db.set(self,'status','Cancelled')

    def update_completed_qty(self, mr_items=None, update_modified=True):
        if self.material_request_type == "Purchase":
            return

        if not mr_items:
            mr_items = [d.name for d in self.get("items")]

        for d in self.get("items"):
            if d.name in mr_items:
                if self.material_request_type in ("Material Issue", "Material Transfer"):
                    d.ordered_qty =  flt(frappe.db.sql("""select sum(transfer_qty)
                        from `tabStock Entry Detail` where material_request = %s
                        and material_request_item = %s and docstatus = 1""",
                        (self.name, d.name))[0][0])

                    if d.ordered_qty and d.ordered_qty > d.qty:
                        frappe.throw(_("The total Issue / Transfer quantity {0} in Material Request {1}  \
                            cannot be greater than requested quantity {2} for Item {3}").format(d.ordered_qty, d.parent, d.qty, d.item_code))

                elif self.material_request_type == "Manufacture":
                    d.ordered_qty = flt(frappe.db.sql("""select sum(qty)
                        from `tabProduction Order` where material_request = %s
                        and material_request_item = %s and docstatus = 1""",
                        (self.name, d.name))[0][0])

                frappe.db.set_value(d.doctype, d.name, "ordered_qty", d.ordered_qty)

        self._update_percent_field({
            "target_dt": "Material Request Item",
            "target_parent_dt": self.doctype,
            "target_parent_field": "per_ordered",
            "target_ref_field": "qty",
            "target_field": "ordered_qty",
            "name": self.name,
        }, update_modified)

    def update_requested_qty(self, mr_item_rows=None):
        """update requested qty (before ordered_qty is updated)"""
        item_wh_list = []
        for d in self.get("items"):
            if (not mr_item_rows or d.name in mr_item_rows) and [d.item_code, d.warehouse] not in item_wh_list \
                    and frappe.db.get_value("Item", d.item_code, "is_stock_item") == 1 and d.warehouse:
                item_wh_list.append([d.item_code, d.warehouse])

        for item_code, warehouse in item_wh_list:
            update_bin_qty(item_code, warehouse, {
                "indented_qty": get_indented_qty(item_code, warehouse)
            })

def update_completed_and_requested_qty(stock_entry, method):
    if stock_entry.doctype == "Stock Entry":
        material_request_map = {}

        for d in stock_entry.get("items"):
            if d.material_request:
                material_request_map.setdefault(d.material_request, []).append(d.material_request_item)

        for mr, mr_item_rows in material_request_map.items():
            if mr and mr_item_rows:
                mr_obj = frappe.get_doc("Material Request", mr)

                if mr_obj.status in ["Stopped", "Cancelled"]:
                    frappe.throw(_("{0} {1} is cancelled or stopped").format(_("Material Request"), mr),
                        frappe.InvalidStatusError)

                mr_obj.update_completed_qty(mr_item_rows)
                mr_obj.update_requested_qty(mr_item_rows)

def set_missing_values(source, target_doc):
    target_doc.run_method("set_missing_values")
    target_doc.run_method("calculate_taxes_and_totals")

def update_item(obj, target, source_parent):
    target.conversion_factor = 1
    target.qty = flt(obj.qty) - flt(obj.ordered_qty)
    target.stock_qty = target.qty

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
    def postprocess(source, target_doc):
        set_missing_values(source, target_doc)

    doclist = get_mapped_doc("Material Request", source_name,   {
        "Material Request": {
            "doctype": "Purchase Order",
            "validation": {
                "docstatus": ["=", 1],
                "material_request_type": ["=", "Purchase"]
            }
        },
        "Material Request Item": {
            "doctype": "Purchase Order Item",
            "field_map": [
                ["name", "material_request_item"],
                ["parent", "material_request"],
                ["uom", "stock_uom"],
                ["uom", "uom"]
            ],
            "postprocess": update_item,
            "condition": lambda doc: doc.ordered_qty < doc.qty
        }
    }, target_doc, postprocess)

    return doclist

@frappe.whitelist()
def make_request_for_quotation(source_name, target_doc=None):
    doclist = get_mapped_doc("Material Request", source_name,   {
        "Material Request": {
            "doctype": "Request for Quotation",
            "validation": {
                "docstatus": ["=", 1],
                "material_request_type": ["=", "Purchase"]
            }
        },
        "Material Request Item": {
            "doctype": "Request for Quotation Item",
            "field_map": [
                ["name", "material_request_item"],
                ["parent", "material_request"],
                ["uom", "uom"]
            ]
        }
    }, target_doc)

    return doclist

@frappe.whitelist()
def make_purchase_order_based_on_supplier(source_name, target_doc=None):
    if target_doc:
        if isinstance(target_doc, basestring):
            import json
            target_doc = frappe.get_doc(json.loads(target_doc))
        target_doc.set("items", [])

    material_requests, supplier_items = get_material_requests_based_on_supplier(source_name)

    def postprocess(source, target_doc):
        target_doc.supplier = source_name

        target_doc.set("items", [d for d in target_doc.get("items")
            if d.get("item_code") in supplier_items and d.get("qty") > 0])

        set_missing_values(source, target_doc)

    for mr in material_requests:
        target_doc = get_mapped_doc("Material Request", mr,     {
            "Material Request": {
                "doctype": "Purchase Order",
            },
            "Material Request Item": {
                "doctype": "Purchase Order Item",
                "field_map": [
                    ["name", "material_request_item"],
                    ["parent", "material_request"],
                    ["uom", "stock_uom"],
                    ["uom", "uom"]
                ],
                "postprocess": update_item,
                "condition": lambda doc: doc.ordered_qty < doc.qty
            }
        }, target_doc, postprocess)

    return target_doc

def get_material_requests_based_on_supplier(supplier):
    supplier_items = [d[0] for d in frappe.db.get_values("Item",
        {"default_supplier": supplier})]
    if supplier_items:
        material_requests = frappe.db.sql_list("""select distinct mr.name
            from `tabMaterial Request` mr, `tabMaterial Request Item` mr_item
            where mr.name = mr_item.parent
            and mr_item.item_code in (%s)
            and mr.material_request_type = 'Purchase'
            and mr.per_ordered < 99.99
            and mr.docstatus = 1
            and mr.status != 'Stopped'
                        order by mr_item.item_code ASC""" % ', '.join(['%s']*len(supplier_items)),
            tuple(supplier_items))
    else:
        material_requests = []
    return material_requests, supplier_items

@frappe.whitelist()
def make_supplier_quotation(source_name, target_doc=None):
    def postprocess(source, target_doc):
        set_missing_values(source, target_doc)

    doclist = get_mapped_doc("Material Request", source_name, {
        "Material Request": {
            "doctype": "Supplier Quotation",
            "validation": {
                "docstatus": ["=", 1],
                "material_request_type": ["=", "Purchase"]
            }
        },
        "Material Request Item": {
            "doctype": "Supplier Quotation Item",
            "field_map": {
                "name": "material_request_item",
                "parent": "material_request"
            }
        }
    }, target_doc, postprocess)

    return doclist

@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
    def update_item(obj, target, source_parent):
        qty = flt(obj.qty) - flt(obj.ordered_qty) \
            if flt(obj.qty) > flt(obj.ordered_qty) else 0
        target.qty = qty
        target.transfer_qty = qty
        target.conversion_factor = 1

        if source_parent.material_request_type == "Material Transfer":
            target.t_warehouse = obj.warehouse
        else:
            target.s_warehouse = obj.warehouse

    def set_missing_values(source, target):
        target.purpose = source.material_request_type
        target.run_method("calculate_rate_and_amount")

    doclist = get_mapped_doc("Material Request", source_name, {
        "Material Request": {
            "doctype": "Stock Entry",
            "validation": {
                "docstatus": ["=", 1],
                "material_request_type": ["in", ["Material Transfer", "Material Issue"]]
            }
        },
        "Material Request Item": {
            "doctype": "Stock Entry Detail",
            "field_map": {
                "name": "material_request_item",
                "parent": "material_request",
                "uom": "stock_uom",
            },
            "postprocess": update_item,
            "condition": lambda doc: doc.ordered_qty < doc.qty
        }
    }, target_doc, set_missing_values)

    return doclist

@frappe.whitelist()
def raise_production_orders(material_request):
    mr= frappe.get_doc("Material Request", material_request)
    errors =[]
    production_orders = []
    default_wip_warehouse = frappe.db.get_single_value("Manufacturing Settings", "default_wip_warehouse")
    for d in mr.items:
        if (d.qty - d.ordered_qty) >0:
            if frappe.db.get_value("BOM", {"item": d.item_code, "is_default": 1}):
                prod_order = frappe.new_doc("Production Order")
                prod_order.production_item = d.item_code
                prod_order.qty = d.qty - d.ordered_qty
                prod_order.fg_warehouse = d.warehouse
                prod_order.wip_warehouse = default_wip_warehouse
                prod_order.description = d.description
                prod_order.stock_uom = d.uom
                prod_order.expected_delivery_date = d.schedule_date
                prod_order.sales_order = d.sales_order
                prod_order.bom_no = get_item_details(d.item_code).bom_no
                prod_order.material_request = mr.name
                prod_order.material_request_item = d.name
                prod_order.planned_start_date = mr.transaction_date
                prod_order.company = mr.company
                prod_order.save()
                production_orders.append(prod_order.name)
            else:
                errors.append(d.item_code + " in Row " + cstr(d.idx))
    if production_orders:
        message = ["""<a href="#Form/Production Order/%s" target="_blank">%s</a>""" % \
            (p, p) for p in production_orders]
        msgprint(_("The following Production Orders were created:" + '\n' + new_line_sep(message)))
    if errors:
        msgprint(_("Productions Orders cannot be raised for:" + '\n' + new_line_sep(errors)))
    return production_orders




@frappe.whitelist()
def get_project_main_items(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql("""select distinct scope_item from `tabProject Costing Schedule`
        where parenttype='Project Initiation' and type_of_cost='External Expenses' and parent='{0}' """.format(filters.get('project')))
