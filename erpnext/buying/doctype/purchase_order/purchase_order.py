# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import cstr, flt
from frappe import msgprint, _
from frappe.model.mapper import get_mapped_doc
from erpnext.controllers.buying_controller import BuyingController
from erpnext.stock.doctype.item.item import get_last_purchase_details
from erpnext.stock.stock_balance import update_bin_qty, get_ordered_qty
from frappe.desk.notifications import clear_doctype_notifications
from frappe.utils.print_format import download_pdf
from frappe.desk.form.load import get_attachments
from frappe.utils.user import get_user_fullname
from frappe.core.doctype.communication.email import make

form_grid_templates = {
	"items": "templates/form_grid/item_grid.html"
}
STANDARD_USERS = ("Guest", "Administrator")

class PurchaseOrder(BuyingController):
	def __init__(self, arg1, arg2=None):
		super(PurchaseOrder, self).__init__(arg1, arg2)
		self.status_updater = [{
			'source_dt': 'Purchase Order Item',
			'target_dt': 'Material Request Item',
			'join_field': 'material_request_item',
			'target_field': 'ordered_qty',
			'target_parent_dt': 'Material Request',
			'target_parent_field': 'per_ordered',
			'target_ref_field': 'qty',
			'source_field': 'stock_qty',
			'percent_join_field': 'material_request',
			'overflow_type': 'order'
		}]

	def validate(self):

		super(PurchaseOrder, self).validate()

		self.set_status()
		pc_obj = frappe.get_doc('Purchase Common')
		pc_obj.validate_for_items(self)
		self.check_for_closed_status(pc_obj)

		self.validate_uom_is_integer("uom", "qty")
		self.validate_uom_is_integer("stock_uom", ["qty", "required_qty"])

		self.validate_with_previous_doc()
		self.validate_for_subcontracting()
		self.validate_minimum_order_qty()
		self.create_raw_materials_supplied("supplied_items")
		self.set_received_qty_for_drop_ship_items()
		if self.get("__islocal"):
			self.validate_project()
			self.title = self.get_title()
		# self.validate_project_items()
		self.vallidate_workflow_transition()

		mr = frappe.get_value('Quotation Opening', filters = {"name": self.quotation_opening, "docstatus": 1}, fieldname = "material_request")
		if mr:
			self.material_request = mr

			proj = frappe.get_value('Quotation Opening', filters = {"name": self.quotation_opening, "docstatus": 1}, fieldname = "project")
			if proj:
				self.project = proj

	def validate_project(self):
		if self.project:
			for item in self.get("items"):
				item.project = self.project
	
	def validate_project_items(self):
		if self.project : 
			warehouse = frappe.db.get_value("Project", self.project, "default_warehouse")
			if not warehouse :
				frappe.throw(_("Set Default Warehouse in Project %s"%self.project))
			else:
				for row in self.get("items"):
					if not row.warehouse :
						row.warehouse = warehouse
					elif row.warehouse !=warehouse : 
						frappe.throw(_("Bad Warehouse in row  %s default warehouse is %s"%(row.idx,warehouse)))

						
	def get_title(self):
		from frappe.utils import getdate
		
		namming =frappe.get_list("Enhanced Nameing Doc", fields=["name","name_of_doc", "index_value","year"],filters={"year": str(getdate(self.transaction_date).year),"name_of_doc":self.doctype},ignore_permissions=True)
		if namming :
			#~ title =self.name[:len(self.naming_series)] + str(getdate(self.transaction_date).year) +"-"+ self.name[len(self.naming_series):]
			title =self.name[:len(self.naming_series)] + str(getdate(self.transaction_date).year) +"-"+ str(namming[0]["index_value"]+1).zfill(5)
			nammeing_doc = frappe.get_doc("Enhanced Nameing Doc",namming[0]["name"])
			nammeing_doc.flags.ignore_permissions = True
			nammeing_doc.index_value = nammeing_doc.index_value+1
			nammeing_doc.save()
			return title
		else : 
			title =self.name[:len(self.naming_series)] + str(getdate(self.transaction_date).year) +"-"+ str(1).zfill(5)
			nammeing_doc = frappe.new_doc("Enhanced Nameing Doc")
			nammeing_doc.flags.ignore_permissions = True
			nammeing_doc.parent = "Enhanced Nameing"
			nammeing_doc.parenttype = "Enhanced Nameing"
			nammeing_doc.parentfield='enhanced_nameing'
			nammeing_doc.naming_series = self.naming_series
			nammeing_doc.index_value = 1
			nammeing_doc.year = str(getdate(self.transaction_date).year)
			nammeing_doc.name_of_doc = self.doctype
			nammeing_doc.save()
			return title
	def on_update(self):
		if hasattr(self,'workflow_state'):
			if self.workflow_state == "Approved By Requester" and not self.project:
				self.handled_by = "Budget Controller"
				# self.set("handled_by", "Budget Controller")

	def before_update_after_submit(self):
		if hasattr(self,'workflow_state'):
			self.flags.ignore_validate_update_after_submit = True
			if self.workflow_state == "Approved By CEO":
				self.set("workflow_state", "Change Terms & Conditions")
				# self.workflow_state = "Change Terms & Conditions"
			# elif self.workflow_state == "Change Terms & Conditions":
			#  	self.flags.ignore_validate_update_after_submit = True
			#  	self.workflow_state = "Reviewed By CEO"

	def on_update_after_submit(self):
		if hasattr(self,'workflow_state'):
			self.flags.ignore_validate_update_after_submit = True
			if self.workflow_state == "Rejected By CEO(tc)":
				frappe.db.set_value("Purchase Order", self.name, "tc_name", self.old_tc_name, update_modified=False)
				frappe.db.set_value("Purchase Order", self.name,"terms", self.old_terms, update_modified=False)
				frappe.db.set_value("Purchase Order", self.name,"payment_plan", self.old_payment_plan, update_modified=False)
				frappe.db.set_value("Purchase Order", self.name,"shipment_terms", self.old_shipment_terms, update_modified=False)
				frappe.db.set_value("Purchase Order", self.name,"definitions", self.old_definitions, update_modified=False)
			

	def vallidate_workflow_transition(self):
		if hasattr(self,'workflow_state'):
			if u"Project Budget Controller" in frappe.get_roles(frappe.session.user) and self.project and self.workflow_state == "Approved By Budget Controller":
					self.workflow_state = "Approved By Project Budget Controller"
			elif u"Budget Controller" in frappe.get_roles(frappe.session.user) and not self.project and self.workflow_state == "Approved By Project Budget Controller":
				self.workflow_state = "Approved By Budget Controller"
			# if u"Shared Services Director" in frappe.get_roles(frappe.session.user):
			# 	if self.project and self.workflow_state == "Approved By Shared Services Director":
			# 		self.workflow_state = "Approved By Shared Services Director (Prt.)"

	def validate_with_previous_doc(self):
		super(PurchaseOrder, self).validate_with_previous_doc({
			"Supplier Quotation": {
				"ref_dn_field": "supplier_quotation",
				"compare_fields": [["supplier", "="], ["company", "="], ["currency", "="]],
			},
			"Supplier Quotation Item": {
				"ref_dn_field": "supplier_quotation_item",
				"compare_fields": [["rate", "="], ["project", "="], ["item_code", "="]],
				"is_child_table": True
			}
		})

	def validate_minimum_order_qty(self):
		items = list(set([d.item_code for d in self.get("items")]))

		itemwise_min_order_qty = frappe._dict(frappe.db.sql("""select name, min_order_qty
			from tabItem where name in ({0})""".format(", ".join(["%s"] * len(items))), items))

		itemwise_qty = frappe._dict()
		for d in self.get("items"):
			itemwise_qty.setdefault(d.item_code, 0)
			itemwise_qty[d.item_code] += flt(d.stock_qty)

		for item_code, qty in itemwise_qty.items():
			if flt(qty) < flt(itemwise_min_order_qty.get(item_code)):
				frappe.throw(_("Item {0}: Ordered qty {1} cannot be less than minimum order qty {2} (defined in Item).").format(item_code,
					qty, itemwise_min_order_qty.get(item_code)))

	def get_schedule_dates(self):
		for d in self.get('items'):
			if d.material_request_item and not d.schedule_date:
				d.schedule_date = frappe.db.get_value("Material Request Item",
						d.material_request_item, "schedule_date")


	def get_last_purchase_rate(self):
		"""get last purchase rates for all items"""

		conversion_rate = flt(self.get('conversion_rate')) or 1.0

		for d in self.get("items"):
			if d.item_code:
				last_purchase_details = get_last_purchase_details(d.item_code, self.name)

				if last_purchase_details:
					d.base_price_list_rate = (last_purchase_details['base_price_list_rate'] *
						(flt(d.conversion_factor) or 1.0))
					d.discount_percentage = last_purchase_details['discount_percentage']
					d.base_rate = last_purchase_details['base_rate'] * (flt(d.conversion_factor) or 1.0)
					d.price_list_rate = d.base_price_list_rate / conversion_rate
					d.rate = d.base_rate / conversion_rate
				else:
					msgprint(_("Last purchase rate not found"))

					item_last_purchase_rate = frappe.db.get_value("Item", d.item_code, "last_purchase_rate")
					if item_last_purchase_rate:
						d.base_price_list_rate = d.base_rate = d.price_list_rate \
							= d.rate = item_last_purchase_rate

	# Check for Closed status
	def check_for_closed_status(self, pc_obj):
		check_list =[]
		for d in self.get('items'):
			if d.meta.get_field('material_request') and d.material_request and d.material_request not in check_list:
				check_list.append(d.material_request)
				pc_obj.check_for_closed_status('Material Request', d.material_request)

	def update_requested_qty(self):
		material_request_map = {}
		for d in self.get("items"):
			if d.material_request_item:
				material_request_map.setdefault(d.material_request, []).append(d.material_request_item)

		for mr, mr_item_rows in material_request_map.items():
			if mr and mr_item_rows:
				mr_obj = frappe.get_doc("Material Request", mr)

				if mr_obj.status in ["Stopped", "Cancelled"]:
					frappe.throw(_("Material Request {0} is cancelled or stopped").format(mr), frappe.InvalidStatusError)

				mr_obj.update_requested_qty(mr_item_rows)

	def update_ordered_qty(self, po_item_rows=None):
		"""update requested qty (before ordered_qty is updated)"""
		item_wh_list = []
		for d in self.get("items"):
			if (not po_item_rows or d.name in po_item_rows) \
				and [d.item_code, d.warehouse] not in item_wh_list \
				and frappe.db.get_value("Item", d.item_code, "is_stock_item") \
				and d.warehouse and not d.delivered_by_supplier:
					item_wh_list.append([d.item_code, d.warehouse])
		for item_code, warehouse in item_wh_list:
			update_bin_qty(item_code, warehouse, {
				"ordered_qty": get_ordered_qty(item_code, warehouse)
			})

	def check_modified_date(self):
		mod_db = frappe.db.sql("select modified from `tabPurchase Order` where name = %s",
			self.name)
		date_diff = frappe.db.sql("select TIMEDIFF('%s', '%s')" % ( mod_db[0][0],cstr(self.modified)))

		if date_diff and date_diff[0][0]:
			msgprint(_("{0} {1} has been modified. Please refresh.").format(self.doctype, self.name),
				raise_exception=True)
				
	def update_status(self, status):
		self.check_modified_date()
		self.set_status(update=True, status=status)
		self.update_requested_qty()
		self.update_ordered_qty()
		self.notify_update()
		clear_doctype_notifications(self)

	def on_submit(self):
		if self.is_against_so():
			self.update_status_updater()

		purchase_controller = frappe.get_doc("Purchase Common")

		self.update_prevdoc_status()
		self.update_requested_qty()
		self.update_ordered_qty()

		frappe.get_doc('Authorization Control').validate_approving_authority(self.doctype,
			self.company, self.base_grand_total)

		purchase_controller.update_last_purchase_rate(self, is_submit = 1)

		# fields = ["tc_name", "terms", "payment_plan", "shipment_terms", "definitions"]
		self.old_tc_name = self.tc_name
		self.old_terms = self.terms
		self.old_payment_plan = self.payment_plan
		self.old_shipment_terms = self.shipment_terms
		self.old_definitions = self.definitions

	def on_cancel(self):
		if self.is_against_so():
			self.update_status_updater()

		if self.has_drop_ship_item():
			self.update_delivered_qty_in_sales_order()

		pc_obj = frappe.get_doc('Purchase Common')
		self.check_for_closed_status(pc_obj)

		frappe.db.set(self,'status','Cancelled')

		self.update_prevdoc_status()

		# Must be called after updating ordered qty in Material Request
		self.update_requested_qty()
		self.update_ordered_qty()

		pc_obj.update_last_purchase_rate(self, is_submit = 0)

	def update_status_updater(self):
		self.status_updater[0].update({
			"target_parent_dt": "Sales Order",
			"target_dt": "Sales Order Item",
			'target_field': 'ordered_qty',
			"join_field": "sales_order_item",
			"target_parent_field": ''
		})

	def update_delivered_qty_in_sales_order(self):
		"""Update delivered qty in Sales Order for drop ship"""
		sales_orders_to_update = []
		for item in self.items:
			if item.sales_order and item.delivered_by_supplier == 1:
				if item.sales_order not in sales_orders_to_update:
					sales_orders_to_update.append(item.sales_order)

		for so_name in sales_orders_to_update:
			so = frappe.get_doc("Sales Order", so_name)
			so.update_delivery_status()
			so.set_status(update=True)
			so.notify_update()

	def has_drop_ship_item(self):
		return any([d.delivered_by_supplier for d in self.items])

	def is_against_so(self):
		return any([d.sales_order for d in self.items if d.sales_order])

	def set_received_qty_for_drop_ship_items(self):
		for item in self.items:
			if item.delivered_by_supplier == 1:
				item.received_qty = item.qty

	def supplier_po_mail(self):
		if self.contact_email:
			full_name = get_user_fullname(frappe.session['user'])
			if full_name == "Guest":
				full_name = "Administrator"

			data = {'contact_email':self.contact_email, 'supplier': self.supplier}
			args = {
				'message': frappe.render_template(self.msg_to_supplier, data),
				'user_fullname': full_name
			}

			subject = _("Purchase Order")
			template = "templates/emails/PO.html"
			sender = frappe.session.user not in STANDARD_USERS and frappe.session.user or None
			message = frappe.get_template(template).render(args)
			attachments = self.get_attachments()
			self.send_email(data, sender, subject, message, attachments)

	def send_email(self, data, sender, subject, message, attachments):
		make(subject = subject, content=message,recipients=data['contact_email'], 
			sender=sender,attachments = attachments, send_email=True,
		     	doctype=self.doctype, name=self.name)["name"]

		frappe.msgprint(_("Email sent to supplier {0}").format(data['supplier']))

	def get_attachments(self):
		attachments = [d.name for d in get_attachments(self.doctype, self.name)]
		attachments.append(frappe.attach_print(self.doctype, self.name, doc=self))
		return attachments

	def has_requester_perm(self):
		if hasattr(self,'workflow_state'):
			pu = frappe.get_value("User Permission", filters = {"allow": "Material Request", "for_value": self.material_request}, fieldname = "user")
			if pu:
				return pu
			else:
				return frappe.session.user

@frappe.whitelist()
def close_or_unclose_purchase_orders(names, status):
	if not frappe.has_permission("Purchase Order", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	names = json.loads(names)
	for name in names:
		po = frappe.get_doc("Purchase Order", name)
		if po.docstatus == 1:
			if status == "Closed":
				if po.status not in ( "Cancelled", "Closed") and (po.per_received < 100 or po.per_billed < 100):
					po.update_status(status)
			else:
				if po.status == "Closed":
					po.update_status("Draft")

	frappe.local.message_log = []

def set_missing_values(source, target):
	target.ignore_pricing_rule = 1
	target.run_method("set_missing_values")
	target.run_method("calculate_taxes_and_totals")

@frappe.whitelist()
def make_purchase_receipt(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		target.qty = flt(obj.qty) - flt(obj.received_qty)
		target.stock_qty = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.conversion_factor)
		target.amount = (flt(obj.qty) - flt(obj.received_qty)) * flt(obj.rate)
		target.base_amount = (flt(obj.qty) - flt(obj.received_qty)) * \
			flt(obj.rate) * flt(source_parent.conversion_rate)

	doc = get_mapped_doc("Purchase Order", source_name,	{
		"Purchase Order": {
			"doctype": "Purchase Receipt",
			"validation": {
				"docstatus": ["=", 1],
			}
		},
		"Purchase Order Item": {
			"doctype": "Purchase Receipt Item",
			"field_map": {
				"name": "purchase_order_item",
				"parent": "purchase_order",
			},
			"postprocess": update_item,
			"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty) and doc.delivered_by_supplier!=1
		},
		"Purchase Taxes and Charges": {
			"doctype": "Purchase Taxes and Charges",
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)

	return doc

@frappe.whitelist()
def make_purchase_invoice(source_name, target_doc=None):
	def postprocess(source, target):
		set_missing_values(source, target)
		#Get the advance paid Journal Entries in Purchase Invoice Advance
		target.set_advances()

	def update_item(obj, target, source_parent):
		target.amount = flt(obj.amount) - flt(obj.billed_amt)
		target.base_amount = target.amount * flt(source_parent.conversion_rate)
		target.qty = target.amount / flt(obj.rate) if (flt(obj.rate) and flt(obj.billed_amt)) else flt(obj.qty)
		
		item = frappe.db.get_value("Item", target.item_code, ["item_group", "buying_cost_center"], as_dict=1)
		target.cost_center = frappe.db.get_value("Project", obj.project, "cost_center") \
			or item.buying_cost_center \
			or frappe.db.get_value("Item Group", item.item_group, "default_cost_center")

	doc = get_mapped_doc("Purchase Order", source_name,	{
		"Purchase Order": {
			"doctype": "Purchase Invoice",
			"validation": {
				"docstatus": ["=", 1],
			}
		},
		"Purchase Order Item": {
			"doctype": "Purchase Invoice Item",
			"field_map": {
				"name": "po_detail",
				"parent": "purchase_order",
			},
			"postprocess": update_item,
			"condition": lambda doc: (doc.base_amount==0 or abs(doc.billed_amt) < abs(doc.amount))
		},
		"Purchase Taxes and Charges": {
			"doctype": "Purchase Taxes and Charges",
			"add_if_empty": True
		}
	}, target_doc, postprocess)

	return doc

@frappe.whitelist()
def make_stock_entry(purchase_order, item_code):
	purchase_order = frappe.get_doc("Purchase Order", purchase_order)

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = "Subcontract"
	stock_entry.purchase_order = purchase_order.name
	stock_entry.supplier = purchase_order.supplier
	stock_entry.supplier_name = purchase_order.supplier_name
	stock_entry.supplier_address = purchase_order.address_display
	stock_entry.company = purchase_order.company
	stock_entry.from_bom = 1
	po_item = [d for d in purchase_order.items if d.item_code == item_code][0]
	stock_entry.fg_completed_qty = po_item.qty
	stock_entry.bom_no = po_item.bom
	stock_entry.get_items()
	return stock_entry.as_dict()

@frappe.whitelist()
def update_status(status, name):
	po = frappe.get_doc("Purchase Order", name)
	po.update_status(status)
	po.update_delivered_qty_in_sales_order()
