# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.model.naming import make_autoname

class BudgetAdjustment(Document):
	def autoname(self):
		self.name = make_autoname(self.get(frappe.scrub(self.budget_against)) 
			+ "/" + self.fiscal_year + "/.###")

	def on_submit(self):
		old_budget = frappe.db.sql("""update tabBudget set docstatus = 0 where name=%s""",self.target_budget)
		target_budget = frappe.get_doc("Budget",self.target_budget)
		target_budget.action_if_annual_budget_exceeded = self.action_if_annual_budget_exceeded
		target_budget.action_if_accumulated_monthly_budget_exceeded = self.action_if_accumulated_monthly_budget_exceeded
		target_budget.monthly_distribution = self.monthly_distribution
		target_budget.budget_template = self.monthly_distribution
		target_budget.accounts = []
		for account in self.accounts :
			ac_child = target_budget.append('accounts')
			ac_child.account = account.account
			ac_child.budget_amount = account.budget_amount
		#~ target_budget.save()
		target_budget.submit()
			

		
	def validate(self):
		if not self.get(frappe.scrub(self.budget_against)):
			frappe.throw(_("{0} is mandatory").format(self.budget_against))
		self.validate_accounts()
		self.set_null_value()
	
	def validate_accounts(self):
		account_list = []
		for d in self.get('accounts'):
			if d.account:
				account_details = frappe.db.get_value("Account", d.account,
					["is_group", "company", "report_type"], as_dict=1)

				if account_details.is_group:
					frappe.throw(_("Budget cannot be assigned against Group Account {0}").format(d.account))
				elif account_details.company != self.company:
					frappe.throw(_("Account {0} does not belongs to company {1}")
						.format(d.account, self.company))
				elif account_details.report_type != "Profit and Loss":
					frappe.throw(_("Budget cannot be assigned against {0}, as it's not an Income or Expense account")
						.format(d.account))

				if d.account in account_list:
					frappe.throw(_("Account {0} has been entered multiple times").format(d.account))
				else:
					account_list.append(d.account)

	def set_null_value(self):
		if self.budget_against == 'Cost Center':
			self.project = None
		else:
			self.cost_center = None


@frappe.whitelist()
def fetch_budget(source_name, target_doc=None):
	#~ frappe.throw(_("{0} is mandatory").format(target_doc))
	target_doc = get_mapped_doc("Budget", source_name, {
		"Budget": {
			"doctype": "Budget",
		},
		"Budget Adjustment": {
			"doctype": "Budget Adjustment",
		}
	}, target_doc)

	return target_doc
