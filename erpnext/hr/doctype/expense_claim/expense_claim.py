# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_fullname, flt
from frappe.model.document import Document
from erpnext.hr.utils import set_employee_name

class InvalidExpenseApproverError(frappe.ValidationError): pass

class ExpenseClaim(Document):
	def get_feed(self):
		return _("{0}: From {0} for {1}").format(self.approval_status,
			self.employee_name, self.total_claimed_amount)

	def validate(self):
		self.validate_sanctioned_amount()
		self.validate_expense_approver()
		self.calculate_total_amount()
		set_employee_name(self)
		self.set_expense_account()
		if self.task and not self.project:
			self.project = frappe.db.get_value("Task", self.task, "project")
		if self.reference_type and self.referance_name and self.reference_type == "Leave Application":
			doc =frappe.get_doc(self.reference_type,self.referance_name)
			doc.expense_claim = self.name
			doc.save(ignore_permissions=True)
		self.validate_emp()
		if self.workflow_state:
			if "Rejected" in self.workflow_state:
				self.docstatus = 1
				self.docstatus = 2

	def validate_emp(self):
		if self.employee:
			employee_user = frappe.get_value("Employee", filters = {"name": self.employee}, fieldname="user_id")
			if self.get('__islocal') and employee_user:
				if u'CEO' in frappe.get_roles(employee_user):
					self.workflow_state = "Created By CEO"
				elif u'Director' in frappe.get_roles(employee_user):
					self.workflow_state = "Created By Director"
				elif u'Manager' in frappe.get_roles(employee_user):
					self.workflow_state = "Created By Manager"
				elif u'Line Manager' in frappe.get_roles(employee_user):
					self.workflow_state = "Created By Line Manager"
				elif u'Employee' in frappe.get_roles(employee_user):
					self.workflow_state = "Pending"

			if not employee_user and self.get('__islocal'):
				self.workflow_state = "Pending"



	def on_submit(self):
		if self.reference_type and self.referance_name and self.reference_type == "Leave Application":
			doc =frappe.get_doc(self.reference_type,self.referance_name)
			doc.expense_claim = self.name
			doc.save(ignore_permissions=True)
		if self.approval_status=="Draft":
			frappe.throw(_("""Approval Status must be 'Approved' or 'Rejected'"""))
		self.update_task_and_project()

	def on_cancel(self):
		self.update_task_and_project()

	def update_task_and_project(self):
		if self.task:
			self.update_task()
		elif self.project:
			frappe.get_doc("Project", self.project).update_project()

	def calculate_total_amount(self):
		self.total_claimed_amount = 0
		self.total_sanctioned_amount = 0
		for d in self.get('expenses'):
			self.total_claimed_amount += flt(d.claim_amount)
			self.total_sanctioned_amount += flt(d.sanctioned_amount)

	def validate_expense_approver(self):
		if self.exp_approver and "Expense Approver" not in frappe.get_roles(self.exp_approver):
			frappe.throw(_("{0} ({1}) must have role 'Expense Approver'")\
				.format(get_fullname(self.exp_approver), self.exp_approver), InvalidExpenseApproverError)

	def update_task(self):
		task = frappe.get_doc("Task", self.task)
		task.update_total_expense_claim()
		task.save()

	def validate_sanctioned_amount(self):
		for d in self.get('expenses'):
			if flt(d.sanctioned_amount) > flt(d.claim_amount):
				frappe.throw(_("Sanctioned Amount cannot be greater than Claim Amount in Row {0}.").format(d.idx))

	def set_expense_account(self):
		for expense in self.expenses:
			if not expense.default_account:
				expense.default_account = get_expense_claim_account(expense.expense_type, self.company)["account"]



def get_permission_query_conditions(user):
	pass
    # if frappe.session.user == "mf.alfarj@tawari.sa":
    #     query = """(True) or (True)"""
    #     return query

@frappe.whitelist()
def get_expense_approver(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""
		select u.name, concat(u.first_name, ' ', u.last_name)
		from tabUser u, tabUserRole r
		where u.name = r.parent and r.role = 'Expense Approver'
		and u.enabled = 1 and u.name like %s
	""", ("%" + txt + "%"))

@frappe.whitelist()
def make_bank_entry(docname):
	from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

	expense_claim = frappe.get_doc("Expense Claim", docname)
	default_bank_cash_account = get_default_bank_cash_account(expense_claim.company, "Bank")

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = 'Bank Entry'
	je.company = expense_claim.company
	je.remark = 'Payment against Expense Claim: ' + docname;

	for expense in expense_claim.expenses:
		je.append("accounts", {
			"account": expense.default_account,
			"debit_in_account_currency": expense.sanctioned_amount,
			"reference_type": "Expense Claim",
			"reference_name": expense_claim.name
		})

	je.append("accounts", {
		"account": default_bank_cash_account.account,
		"credit_in_account_currency": expense_claim.total_sanctioned_amount,
		"reference_type": "Expense Claim",
		"reference_name": expense_claim.name,
		"balance": default_bank_cash_account.balance,
		"account_currency": default_bank_cash_account.account_currency,
		"account_type": default_bank_cash_account.account_type
	})

	return je.as_dict()

@frappe.whitelist()
def get_expense_claim_account(expense_claim_type, company):
	account = frappe.db.get_value("Expense Claim Account",
		{"parent": expense_claim_type, "company": company}, "default_account")

	if not account:
		frappe.throw(_("Please set default account in Expense Claim Type {0}")
			.format(expense_claim_type))

	return {
		"account": account
	}
