# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.csvutils import UnicodeWriter
from frappe.utils import cstr, add_days, date_diff, getdate , nowdate
import datetime
from datetime import date



class UploadJournalEntry(Document):

	def load_file(self):
		import xlrd
		from xlrd import open_workbook
		if(self.excel_file):
			wb = open_workbook(frappe.local.site + "/public" + self.excel_file)
			sheet = wb.sheets()[0]
			if(sheet):
				number_of_rows = sheet.nrows
				number_of_columns = sheet.ncols
				items = []
				rows = []
				self.excel_data = {}
				accounts = []
				supplier_invoice_date=""
				for row in range(1, number_of_rows):
					account=(sheet.cell(row,0).value)
					cost_center=(sheet.cell(row,1).value)
					party_type=(sheet.cell(row,2).value)
					party=(sheet.cell(row,3).value)
					debit=(sheet.cell(row,4).value)
					credit=(sheet.cell(row,5).value)
					reference_type=(sheet.cell(row,6).value)
					reference_name=(sheet.cell(row,7).value)
					project=(sheet.cell(row,8).value)
					is_advance=(sheet.cell(row,9).value)
					reason_code=(sheet.cell(row,10).value)
					description=(sheet.cell(row,11).value)
					supplier=(sheet.cell(row,12).value)
					if (sheet.cell(row,13).value):
						supplier_invoice_date=datetime.datetime(*xlrd.xldate_as_tuple(sheet.cell(row,13).value,wb.datemode))
					supplier_invoice_no=(sheet.cell(row,14).value)
					supplier_vat_id=(sheet.cell(row,15).value)
					vat = (sheet.cell(row,16).value)
					if (vat == 5):
						vat_value = "5"
					else :
						vat_value = "15"


					accounts_row={ "doctype": "Journal Entry Account", "account": account, "cost_center": cost_center, "party_type": party_type, "party": party ,"debit_in_account_currency": debit, "credit_in_account_currency": credit , "reference_type": reference_type,
					 				"reference_name":reference_name,"project":project,"is_advance":is_advance,"reason_code":reason_code,"description":description,"supplier":supplier,"supplier_invoice_date":supplier_invoice_date,"supplier_invoice_no":supplier_invoice_no,"supplier_vat_id":supplier_vat_id,"vat_value2":vat_value}
					accounts.append(accounts_row)

				journal_entry = frappe.get_doc({
				"doctype":"Journal Entry",
				"voucher_type":"Journal Entry",
				"posting_date": frappe.utils.nowdate(),
				"accounts":accounts

				})
				journal_entry.flags.ignore_mandatory = True
				# journal_entry.flags.ignore_permissions = True
				journal_entry.save()
		        # frappe.db.commit()
				msg = """<b><a href="#Form/Journal Entry/{pp}">{pp}</a></b> """.format(pp = journal_entry.name)
				self.je = journal_entry.name
				frappe.msgprint(("Journal Entry has been created:") +msg)



		else:
			frappe.throw("Upload an Excel file To load data!")


@frappe.whitelist()
def get_template():
	if not frappe.has_permission("Upload Journal Entry", "create"):
		raise frappe.PermissionError

	args = frappe.local.form_dict

	w = UnicodeWriter()
	w = add_header(w)

	# w = add_data(w, args)

	# write out response as a type csv
	frappe.response['result'] = cstr(w.getvalue())
	frappe.response['type'] = 'csv'
	frappe.response['doctype'] = "Upload Journal Entry"

def add_header(w):
	# voucher_type = ", ".join((frappe.get_meta("Upload Journal Entry").get_field("voucher_type").options or "").strip().split("\n"))
	w.writerow(["Notes:"])
	w.writerow(["Please do not change the template headings"])
	# w.writerow(["Entry Type should be one of these values: " + voucher_type])
	w.writerow(["If you are overwriting existing Upload Journal Entry records, 'ID' column mandatory"])
	w.writerow(["ID", "Employee", "Employee Name", "Date", "Status", "Leave Type",
		 "Company", "Naming Series"])
	return w
