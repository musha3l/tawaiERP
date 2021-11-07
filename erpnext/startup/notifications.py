# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

def get_notification_config():
	return { 
		"for_doctype": {
			# "Governmental Documents": {
			# "is_message": ("=", 1)
			# },
			# "Employee": {
			# "is_message": ("=", 1)
			# },
			# "Health Insurance Info": {
			# "is_message": ("=", 1)
			# },	
			# "Issue": {"status": "Open"},
			# "Warranty Claim": {"status": "Open"},
			# "Task": {"status": ("in", ("Open", "Overdue"))},
			# "Project": {"status": "Open"},
			# "Item": {"total_projected_qty": ("<", 0)},
			# "Customer": {"status": "Open"},
			# "Supplier": {"status": "Open"},
			# "Lead": {"status": "Open"},
			# "Contact": {"status": "Open"},
			# "Opportunity": {"status": "Open"},
			# "Quotation": {"docstatus": 0},
			# "Sales Order": {
			# 	"status": ("not in", ("Completed", "Closed")),
			# 	"docstatus": ("<", 2)
			# },
			# "Journal Entry": {"docstatus": 0},
			# "Sales Invoice": {
			# 	"outstanding_amount": (">", 0),
			# 	"docstatus": ("<", 2)
			# },
			# "Purchase Invoice": {
			# 	"outstanding_amount": (">", 0),
			# 	"docstatus": ("<", 2)
			# },
			# "Payment Entry": {"docstatus": 0},
			# "Expense Claim": {"approval_status": "Draft"},
			# "Job Applicant": {"status": "Open"},
			# "Delivery Note": {
			# 	"status": ("not in", ("Completed", "Closed")),
			# 	"docstatus": ("<", 2)
			# },
			# "Stock Entry": {"docstatus": 0},
			# "Material Request": {
			# 	"docstatus": ("<", 2),
			# 	"status": ("not in", ("Stopped",)),
			# 	"per_ordered": ("<", 100)
			# },
			# "Request for Quotation": { "docstatus": 0 },
			# "Supplier Quotation": {"docstatus": 0},
			# "Purchase Order": {
			# 	"status": ("not in", ("Completed", "Closed")),
			# 	"docstatus": ("<", 2)
			# },
			# "Purchase Receipt": {
			# 	"status": ("not in", ("Completed", "Closed")),
			# 	"docstatus": ("<", 2)
			# },
			# "Production Order": { "status": ("in", ("Draft", "Not Started", "In Process")) },
			# "BOM": {"docstatus": 0},
			# "Timesheet": {"status": "Draft"},
		}
	}

