# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class AssetsBarcode(Document):
	def load_barcode_cat(self,category):
		if category == "All":
			asset_list = frappe.get_list("Asset", {},["name","barcode_img"])
		else:
			asset_list = frappe.get_list("Asset", {"asset_category":category},["name","barcode_img"])
		
		return asset_list

def load_barcode_cat_test():
		asset_list = frappe.get_list("Asset", {"asset_category":"CARS"},["name","barcode_img"])
		
		return asset_list