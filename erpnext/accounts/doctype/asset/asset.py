# -*- coding: utf-8 -*-
# Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, add_months, cint, nowdate, getdate, get_last_day, date_diff, add_days
from frappe.model.document import Document
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import get_fixed_asset_account
from erpnext.accounts.doctype.asset.depreciation \
	import get_disposal_account_and_cost_center, get_depreciation_accounts
from frappe.model.naming import make_autoname

import barcode
from PIL import Image

from barcode.writer import ImageWriter
from erpnext.accounts.general_ledger import make_gl_entries
from erpnext.controllers.accounts_controller import AccountsController

class Asset(AccountsController):

	def autoname(self):
		from frappe.model.naming import make_autoname
		asset_category = frappe.get_doc("Asset Category",self.asset_category)
		asset_name = frappe.get_all("Asset Name", fields=["naming_series"],
				filters={"asset_category": self.asset_category })
		if asset_name :
			self.naming_series = asset_name[0]["naming_series"]
		else :
			current = asset_category.name
			while  current :
				current = asset_category.parent_asset_category
				if current:
					asset_category = frappe.get_doc("Asset Category",current)
					asset_name = frappe.get_all("Asset Name", fields=["naming_series"],
						filters={"asset_category": asset_category.name})
					if asset_name :
						self.naming_series = asset_name[0]["naming_series"]
						break
		self.name = make_autoname(self.naming_series+'.#####')

	# API for Generate Barcode Button
	# js calls api and give it name of image
	def barcode_attach2(self,name):
		#~ try:
		# frappe.throw(str(name))
		barcode_path = frappe.get_site_path()+'/public/files/'
		print (name)

		code39 = barcode.codex.Code39( name, None,  add_checksum=False)
		#~ code39 = barcode.get('code39', name, writer=None, add_checksum=False)
		print (code39.get_fullcode())
		filename = code39.save(barcode_path+name)


		#~ barcode_class = barcode.get_barcode_class('code39')
		#~ ean = barcode_class(name, ImageWriter(), add_checksum=False)
		#~ ean.save(barcode_path+name)

		self.save_image("/files/", name + '.svg')

		img_path = "/files/" + name + ".svg"

		frappe.db.sql("""update `tabAsset` set barcode_img = %s
			where name = %s""", (img_path, name))
		frappe.db.commit()

		return img_path

		#~ except Exception as e:
			#~ raise e


	def barcode_attach(self):
	    barcode_class = barcode.get_barcode_class('code39')
	    ean = barcode_class(self.name, ImageWriter(), add_checksum=False)
	    barcode_path = frappe.get_site_path()+'/public/files/'

	    ean.save(barcode_path+self.name)
	    # ean.save(barcode_path+self.name+'.png')

	    self.save_image("/files/",self.name + '.png')

	def save_image(self,path, name):
	    # save barcode image to file table
	    attach_image = frappe.get_doc({
	        "doctype": "File",
	        "file_name": name,
	        "file_url": path + name,
	        "folder":"home"
	    })

	    attach_image.insert()
	    #~ barcode_path = frappe.get_site_path()+'/public/files/'
	    #~ im = Image.open(barcode_path +name)
	    #~ im.thumbnail((200,60),Image.ANTIALIAS)
	    #~ im = im.resize((300,120),Image.ANTIALIAS)
	    #~ im.save(barcode_path +name,quality=90)

	def after_insert(self):
	    img_path = "/files/" + self.name + ".png"

	    frappe.db.sql("""update `tabAsset` set barcode_img = %s
	        where name = %s""", (img_path, self.name))
	    frappe.db.commit()


	def validate(self):
		self.status = self.get_status()
		self.validate_item()
		self.set_missing_values()
		self.validate_asset_values()
		self.make_depreciation_schedule()
		self.set_accumulated_depreciation()
		self.validate_expected_value_after_useful_life()
		# Validate depreciation related accounts
		get_depreciation_accounts(self)
		# attache barcode image
		self.barcode_attach()


	def on_submit(self):
		self.set_status()
		if self.is_existing_asset:
			self.make_gl_entries()

	def on_cancel(self):
		self.validate_cancellation()
		self.delete_depreciation_entries()
		self.set_status()
		self.make_gl_entries(cancel=1)

	def make_gl_entries(self, cancel=0, adv_adj=0):
		gl_entries = []
		self.add_gl_entries(gl_entries)
		make_gl_entries(gl_entries, cancel=cancel, adv_adj=adv_adj)

	def add_gl_entries(self, gl_entries):
		#~ pass
		if not self.credit_to :
			frappe.throw(_("Credit To Account Missing"))
		if not self.debit_to :
			frappe.throw(_("Debit To Account Missing"))

		gl_entries.append(
			self.get_gl_dict({
				"account": self.credit_to,
				#~ "account_currency": self.paid_from_account_currency,
				"against": self.debit_to,
				"credit_in_account_currency": self.gross_purchase_amount,
				"credit": self.gross_purchase_amount,
				"against_voucher_type": self.doctype,
				"against_voucher": self.name
			})
		)
		gl_entries.append(
			self.get_gl_dict({
				"account": self.debit_to,
				#~ "account_currency": self.paid_to_account_currency,
				"against": self.credit_to,
				"debit_in_account_currency": self.gross_purchase_amount,
				"debit": self.gross_purchase_amount,
				"against_voucher_type": self.doctype,
				"against_voucher": self.name
			})
		)


	def validate_item(self):
		item = frappe.db.get_value("Item", self.item_code,
			["is_fixed_asset", "is_stock_item", "disabled"], as_dict=1)
		if not item:
			frappe.throw(_("Item {0} does not exist").format(self.item_code))
		elif item.disabled:
			frappe.throw(_("Item {0} has been disabled").format(self.item_code))
		elif not item.is_fixed_asset:
			frappe.throw(_("Item {0} must be a Fixed Asset Item").format(self.item_code))
		elif item.is_stock_item:
			frappe.throw(_("Item {0} must be a non-stock item").format(self.item_code))

	def set_missing_values(self):
		if self.item_code:
			item_details = get_item_details(self.item_code)
			for field, value in item_details.items():
				if not self.get(field):
					self.set(field, value)

		self.value_after_depreciation = (flt(self.gross_purchase_amount) -
			flt(self.opening_accumulated_depreciation))

	def validate_asset_values(self):
		if flt(self.expected_value_after_useful_life) >= flt(self.gross_purchase_amount):
			frappe.throw(_("Expected Value After Useful Life must be less than Gross Purchase Amount"))

		if not flt(self.gross_purchase_amount):
			frappe.throw(_("Gross Purchase Amount is mandatory"), frappe.MandatoryError)

		if not self.is_existing_asset:
			self.opening_accumulated_depreciation = 0
			self.number_of_depreciations_booked = 0
			if not self.next_depreciation_date:
				frappe.throw(_("Next Depreciation Date is mandatory for new asset"))
		else:
			depreciable_amount = flt(self.gross_purchase_amount) - flt(self.expected_value_after_useful_life)
			if flt(self.opening_accumulated_depreciation) > depreciable_amount:
					frappe.throw(_("Opening Accumulated Depreciation must be less than equal to {0}")
						.format(depreciable_amount))

			if self.opening_accumulated_depreciation:
				if not self.number_of_depreciations_booked:
					frappe.throw(_("Please set Number of Depreciations Booked"))
			else:
				self.number_of_depreciations_booked = 0

			if cint(self.number_of_depreciations_booked) > cint(self.total_number_of_depreciations):
				frappe.throw(_("Number of Depreciations Booked cannot be greater than Total Number of Depreciations"))

		if self.next_depreciation_date and getdate(self.next_depreciation_date) < getdate(nowdate()):
			frappe.msgprint(_("Next Depreciation Date is entered as past date"))

		if (flt(self.value_after_depreciation) > flt(self.expected_value_after_useful_life)
			and not self.next_depreciation_date):
				frappe.throw(_("Please set Next Depreciation Date"))

	def make_depreciation_schedule(self):
		# import datetime
		# import time
		# from datetime import datetime
		# from datetime import timedelta
		# import dateutil.parser

		if self.depreciation_method != 'Manual':
			self.schedules = []
		if not self.get("schedules") and self.next_depreciation_date:
			pi_last_month_day = get_last_day(getdate(self.purchase_date))
			# added_month = 0
			# rest_of_month_days = 0
			# if getdate(self.next_depreciation_date) > getdate(self.purchase_date):
			# 	added_month = 1
			# 	rest_of_month_days = cint(getdate(self.purchase_date).day)
			# 	last_month_day = get_last_day(getdate(self.next_depreciation_date))
			# 	date_difference = cint(date_diff(last_month_day, self.purchase_date))
			# 	depreciation_amount = self.get_depreciation_amount(flt(self.value_after_depreciation))*(float(date_difference/30.0))
			# 	self.append("schedules", {
			# 		"schedule_date": last_month_day,
			# 		"depreciation_amount": depreciation_amount
			# 	})
			# 	rest_of_days_deduction = (flt(self.value_after_depreciation)*(float(rest_of_month_days/30.0)/cint(self.total_number_of_depreciations)))
			# 	total_deductions = (flt(self.value_after_depreciation)*(float(rest_of_month_days/30.0)/cint(self.total_number_of_depreciations))) + \
			# 	(flt(self.value_after_depreciation)*(float(date_difference/30.0)/cint(self.total_number_of_depreciations)))

			# 	self.value_after_depreciation -= total_deductions
			# 	self.number_of_depreciations_booked = 1
			value_after_depreciation = flt(self.value_after_depreciation)

			number_of_pending_depreciations = cint(self.total_number_of_depreciations) - \
				cint(self.number_of_depreciations_booked)
			if number_of_pending_depreciations:
				for n in xrange(number_of_pending_depreciations):
					schedule_date = add_months(self.next_depreciation_date, n * cint(self.frequency_of_depreciation))
					last_month_day = get_last_day(getdate(schedule_date))
					if n== 0 and getdate(self.next_depreciation_date) > getdate(self.purchase_date):
						init_depreciation_amount = self.get_depreciation_amount(value_after_depreciation)
						rest_of_month_days = cint(getdate(self.purchase_date).day)
						depreciation_amount = init_depreciation_amount - (init_depreciation_amount * (flt(getdate(self.purchase_date).day-1)/cint(getdate(pi_last_month_day).day)))
						# frappe.throw(str(flt(date_difference)/cint(getdate(pi_last_month_day).day)))
					else:
						depreciation_amount = self.get_depreciation_amount(value_after_depreciation)
					value_after_depreciation -= flt(depreciation_amount)

					self.append("schedules", {
						"schedule_date": last_month_day,
						"depreciation_amount": flt(depreciation_amount)
					})
			if getdate(self.next_depreciation_date) > getdate(self.purchase_date) and number_of_pending_depreciations:
				end_date = add_days(last_month_day, rest_of_month_days)
				end_date_last_month = (get_last_day(getdate(end_date)))
				# # start_date = add_days(last_month_day, 1)
				# # frappe.throw(str(start_date))
				date_difference = cint(date_diff(get_last_day(getdate(self.purchase_date)), self.purchase_date))
				depreciation_amount = init_depreciation_amount - (init_depreciation_amount * (flt(date_difference+1)/cint(getdate(pi_last_month_day).day)))
				if flt(depreciation_amount) > 0:
					self.append("schedules", {
						"schedule_date": end_date_last_month,
						"depreciation_amount": flt(depreciation_amount)
					})
			# value_after_depreciation = flt(self.value_after_depreciation)

			# number_of_pending_depreciations = cint(self.total_number_of_depreciations) - \
			# 	cint(self.number_of_depreciations_booked)

			# next_depre=datetime.strptime(self.next_depreciation_date,'%Y-%m-%d')

			# dYear = next_depre.strftime("%Y")
			# dMonth = str(int(next_depre.strftime("%m"))%12+1)
			# dDay = "1"
			# nextMonth = datetime.strptime(dYear+"-"+dMonth+"-"+ dDay,'%Y-%m-%d')
			# delta = timedelta(seconds=1)
			# dt= nextMonth - delta
			# dd=datetime.combine(dt,datetime.min.time()).date()
			# dayss= (int((dd-next_depre.date()).days))+1

			# if number_of_pending_depreciations:


			# 	if number_of_pending_depreciations >0:
			# 		depreciation_amount = (self.get_depreciation_amount(value_after_depreciation))*(float(dayss)/30.0)
			# 		value_after_depreciation -= flt(depreciation_amount)
			# 		if dayss != 0:
			# 			self.append("schedules", {
			# 					"schedule_date": dd,
			# 					"depreciation_amount": depreciation_amount
			# 				})


			# 	for n in xrange(1,number_of_pending_depreciations):
			# 		schedule_date = add_months(dd,
			# 			n * cint(self.frequency_of_depreciation))

			# 		depreciation_amount = self.get_depreciation_amount(value_after_depreciation)
			# 		value_after_depreciation -= flt(depreciation_amount)

			# 		self.append("schedules", {
			# 			"schedule_date": schedule_date,
			# 			"depreciation_amount": depreciation_amount
			# 		})

			# 	schedule_date = add_months(dd,
			# 		(number_of_pending_depreciations) * cint(self.frequency_of_depreciation))
			# 	depreciation_amount2 = (self.get_depreciation_amount(value_after_depreciation))*((30.0-float(dayss))/30.0)

			# 	depreciation_amount = self.get_depreciation_amount(value_after_depreciation)
			# 	value_after_depreciation = value_after_depreciation -depreciation_amount2

			# 	self.append("schedules", {
			# 		"schedule_date": schedule_date,
			# 		"depreciation_amount": depreciation_amount2
			# 	})

			# 	if dayss==0:
			# 		self.append("schedules", {
			# 					"schedule_date": add_months(dd,number_of_pending_depreciations * cint(self.frequency_of_depreciation)),
			# 					"depreciation_amount": self.get_depreciation_amount(value_after_depreciation)
			# 				})


	def set_accumulated_depreciation(self):
		accumulated_depreciation = flt(self.opening_accumulated_depreciation)
		for d in self.get("schedules"):
			accumulated_depreciation  += flt(d.depreciation_amount)
			d.accumulated_depreciation_amount = flt(accumulated_depreciation)

	def get_depreciation_amount(self, depreciable_value):
		if self.depreciation_method in ("Straight Line", "Manual"):
			depreciation_amount = (flt(self.value_after_depreciation) -
				flt(self.expected_value_after_useful_life)) / (flt(self.total_number_of_depreciations) -
				cint(self.number_of_depreciations_booked)) #flt total_number_of_depreciations
		else:
			factor = 200.0 /  flt(self.total_number_of_depreciations) #flt total_number_of_depreciations
			depreciation_amount = flt(depreciable_value * factor / 100, 0)

			value_after_depreciation = flt(depreciable_value) - depreciation_amount
			if value_after_depreciation < flt(self.expected_value_after_useful_life):
				depreciation_amount = flt(depreciable_value) - flt(self.expected_value_after_useful_life)

		return depreciation_amount

	def validate_expected_value_after_useful_life(self):
		accumulated_depreciation_after_full_schedule = \
			max([d.accumulated_depreciation_amount for d in self.get("schedules")])

		asset_value_after_full_schedule = (flt(self.gross_purchase_amount) -
			flt(accumulated_depreciation_after_full_schedule))

		# if self.expected_value_after_useful_life < asset_value_after_full_schedule:
		# 	frappe.throw(_("Expected value after useful life must be greater than or equal to {0}")
		# 		.format(asset_value_after_full_schedule))

	def validate_cancellation(self):
		if self.status not in ("Submitted", "Partially Depreciated", "Fully Depreciated"):
			frappe.throw(_("Asset cannot be cancelled, as it is already {0}").format(self.status))

		if self.purchase_invoice:
			frappe.throw(_("Please cancel Purchase Invoice {0} first").format(self.purchase_invoice))

	def delete_depreciation_entries(self):
		for d in self.get("schedules"):
			if d.journal_entry:
				frappe.get_doc("Journal Entry", d.journal_entry).cancel()
				d.db_set("journal_entry", None)

		self.db_set("value_after_depreciation",
			(flt(self.gross_purchase_amount) - flt(self.opening_accumulated_depreciation)))

	def set_status(self, status=None):
		'''Get and update status'''
		if not status:
			status = self.get_status()
		self.db_set("status", status)

	def get_status(self):
		'''Returns status based on whether it is draft, submitted, scrapped or depreciated'''
		if self.docstatus == 0:
			status = "Draft"
		elif self.docstatus == 1:
			status = "Submitted"
			if self.journal_entry_for_scrap:
				status = "Scrapped"
			elif flt(self.value_after_depreciation) <= flt(self.expected_value_after_useful_life):
				status = "Fully Depreciated"
			elif flt(self.value_after_depreciation) < flt(self.gross_purchase_amount):
				status = 'Partially Depreciated'
		elif self.docstatus == 2:
			status = "Cancelled"

		return status

@frappe.whitelist()
def make_purchase_invoice(asset, item_code, gross_purchase_amount, company, posting_date):
	pi = frappe.new_doc("Purchase Invoice")
	pi.company = company
	pi.currency = frappe.db.get_value("Company", company, "default_currency")
	pi.posting_date = posting_date
	pi.append("items", {
		"item_code": item_code,
		"is_fixed_asset": 1,
		"asset": asset,
		"expense_account": get_fixed_asset_account(asset),
		"qty": 1,
		"price_list_rate": gross_purchase_amount,
		"rate": gross_purchase_amount
	})
	pi.set_missing_values()
	return pi

@frappe.whitelist()
def make_sales_invoice(asset, item_code, company):
	si = frappe.new_doc("Sales Invoice")
	si.company = company
	si.currency = frappe.db.get_value("Company", company, "default_currency")
	disposal_account, depreciation_cost_center = get_disposal_account_and_cost_center(company)
	si.append("items", {
		"item_code": item_code,
		"is_fixed_asset": 1,
		"asset": asset,
		"income_account": disposal_account,
		"cost_center": depreciation_cost_center,
		"qty": 1
	})
	si.set_missing_values()
	return si

@frappe.whitelist()
def transfer_asset(args):
	import json
	args = json.loads(args)
	movement_entry = frappe.new_doc("Asset Movement")
	movement_entry.update(args)
	movement_entry.insert()
	movement_entry.submit()

	frappe.db.commit()

	frappe.msgprint(_("Asset Movement record {0} created").format("<a href='#Form/Asset Movement/{0}'>{0}</a>".format(movement_entry.name)))

@frappe.whitelist()
def get_item_details(item_code):
	asset_category = frappe.db.get_value("Item", item_code, "asset_category")

	if not asset_category:
		frappe.throw(_("Please enter Asset Category in Item {0}").format(item_code))

	ret = frappe.db.get_value("Asset Category", asset_category,
		["depreciation_method", "total_number_of_depreciations", "frequency_of_depreciation"], as_dict=1)

	ret.update({
		"asset_category": asset_category
	})

	return ret

@frappe.whitelist()
def get_item_details_with_company(item_code , company):
	asset_category = frappe.db.get_value("Item", item_code, "asset_category")

	if not asset_category:
		frappe.throw(_("Please enter Asset Category in Item {0}").format(item_code))


	debit_to = frappe.db.get_value("Asset Category Account",
			filters={"parent": asset_category, "company_name": company}, fieldname="fixed_asset_account")

	if not debit_to:
		frappe.throw(_("Please add Asset Category account").format(item_code))

	ret = frappe.db.get_value("Asset Category", asset_category,
		["depreciation_method", "total_number_of_depreciations", "frequency_of_depreciation"], as_dict=1)

	ret.update({
		"asset_category": asset_category,
		"debit_to":debit_to
	})

	return ret
