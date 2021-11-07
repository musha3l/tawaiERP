# encoding: utf-8
# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, cstr
from frappe import _
from erpnext.accounts.utils import get_account_currency

def execute(filters=None):
	account_details = {}
	for acc in frappe.db.sql("""select name, is_group from tabAccount""", as_dict=1):
		account_details.setdefault(acc.name, acc)

	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [
		_("Posting Date") + ":Date:90",
		_("VAT %") + "::50",
		_("Supplier Invoice Date") + ":Date:150", _("Account") + ":Link/Account:200",
		_("Debit") + ":Float:100", _("Credit") + ":Float:100"
	]

	columns += [
		_("Voucher Type") + "::120",
		_("Voucher No") + ":Dynamic Link/"+_("Voucher Type")+":160",
		_("Supplier Invoice No") + "::150",
		_("Party Type") + "::120",
		_("Party Name") + "::200",
		_("Supplier VAT ID") + "::150",
		_("Description") + "::800",

	]

	return columns

def get_data(filters):
	data =[]
	descs=''


	gl_list=frappe.db.sql(""" select name,posting_date,account,debit,credit,voucher_type,voucher_no,description from `tabGL Entry` where (voucher_type='Purchase Invoice' or voucher_type='Sales Invoice') and (account='22290001-RECEIVABLE VAT -ضريبة قيمة مضافة قابلة للخصم - T 15% - T' or account='22290001-RECEIVABLE VAT -ضريبة قيمة مضافة قابلة للخصم - T 5% - T' or account='22290002-PAYABLE VAT - ضريبة قيمة مضافة مستحقة -T - 15% - T'or account='22290002-PAYABLE VAT - ضريبة قيمة مضافة مستحقة -T - 5%  - T') order by posting_date asc""",as_dict=1)
	# bill_date=""
	# bill_no=""
	# supplier_vat_id=""
	# description=""
	for gl in gl_list:
		if gl.voucher_type == 'Purchase Invoice':
			purchase_invoice = frappe.db.sql("select supplier_name,bill_date,bill_no,supplier_vat_id from `tabPurchase Invoice` where name='{0}' ".format(gl.voucher_no))
			pi_desc = frappe.db.sql ("select description from `tabPurchase Invoice Item` where parent ='{0}'".format(gl.voucher_no))
			vat_value = frappe.db.sql ("select rate from `tabPurchase Taxes and Charges` where parent ='{0}'".format(gl.voucher_no))
			description=''
			for desc in pi_desc:
				descs+= desc[0]+','
			if filters.get("filter_by_supplier"):
				if filters.get("vat_value"):
					if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
						if purchase_invoice[0][1]:
							if purchase_invoice[0][1] >= getdate(filters.from_date) and purchase_invoice[0][1] <= getdate(filters.to_date) and filters.get("account") == gl.account and flt(filters.get("vat_value")) == vat_value[0][0]:
								supplier_name = purchase_invoice[0][0]
								bill_date = purchase_invoice[0][1]
								bill_no = purchase_invoice[0][2]
								supplier_vat_id = purchase_invoice[0][3]
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Supplier",
								supplier_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("from_date") and filters.get("to_date"):
						if purchase_invoice[0][1]:
							if purchase_invoice[0][1] >= getdate(filters.from_date) and purchase_invoice[0][1] <= getdate(filters.to_date) and flt(filters.get("vat_value")) == vat_value[0][0]:
								supplier_name = purchase_invoice[0][0]
								bill_date = purchase_invoice[0][1]
								bill_no = purchase_invoice[0][2]
								supplier_vat_id = purchase_invoice[0][3]
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Supplier",
								supplier_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("account"):
						if filters.get("account") == gl.account and flt(filters.get("vat_value")) == vat_value[0][0]:
							supplier_name = purchase_invoice[0][0]
							bill_date = purchase_invoice[0][1]
							bill_no = purchase_invoice[0][2]
							supplier_vat_id = purchase_invoice[0][3]
							description= pi_desc[0][0]
							row = [
							gl.posting_date,
							vat_value[0][0],
							bill_date,
							gl.account,
							gl.debit,
							gl.credit,
							gl.voucher_type,
							gl.voucher_no,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

					else:
						if flt(filters.get("vat_value")) == vat_value[0][0]:
							supplier_name = purchase_invoice[0][0]
							bill_date = purchase_invoice[0][1]
							bill_no = purchase_invoice[0][2]
							supplier_vat_id = purchase_invoice[0][3]
							description= pi_desc[0][0]
							row = [
							gl.posting_date,
							vat_value[0][0],
							bill_date,
							gl.account,
							gl.debit,
							gl.credit,
							gl.voucher_type,
							gl.voucher_no,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)
				else:
					if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
						if purchase_invoice[0][1]:
							if purchase_invoice[0][1] >= getdate(filters.from_date) and purchase_invoice[0][1] <= getdate(filters.to_date) and filters.get("account") == gl.account:
								supplier_name = purchase_invoice[0][0]
								bill_date = purchase_invoice[0][1]
								bill_no = purchase_invoice[0][2]
								supplier_vat_id = purchase_invoice[0][3]
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Supplier",
								supplier_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("from_date") and filters.get("to_date"):
						if purchase_invoice[0][1]:
							if purchase_invoice[0][1] >= getdate(filters.from_date) and purchase_invoice[0][1] <= getdate(filters.to_date):
								supplier_name = purchase_invoice[0][0]
								bill_date = purchase_invoice[0][1]
								bill_no = purchase_invoice[0][2]
								supplier_vat_id = purchase_invoice[0][3]
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Supplier",
								supplier_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("account"):
						if filters.get("account") == gl.account:
							supplier_name = purchase_invoice[0][0]
							bill_date = purchase_invoice[0][1]
							bill_no = purchase_invoice[0][2]
							supplier_vat_id = purchase_invoice[0][3]
							description= pi_desc[0][0]
							row = [
							gl.posting_date,
							vat_value[0][0],
							bill_date,
							gl.account,
							gl.debit,
							gl.credit,
							gl.voucher_type,
							gl.voucher_no,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

					else:
						supplier_name = purchase_invoice[0][0]
						bill_date = purchase_invoice[0][1]
						bill_no = purchase_invoice[0][2]
						supplier_vat_id = purchase_invoice[0][3]
						description= pi_desc[0][0]
						row = [
						gl.posting_date,
						vat_value[0][0],
						bill_date,
						gl.account,
						gl.debit,
						gl.credit,
						gl.voucher_type,
						gl.voucher_no,
						bill_no,
						"Supplier",
						supplier_name,
						supplier_vat_id,
						description
						]
						data.append(row)
			else:
				if filters.get("vat_value"):
					if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
						if gl.posting_date:
							if gl.posting_date >= getdate(filters.from_date) and gl.posting_date <= getdate(filters.to_date) and filters.get("account") == gl.account and flt(filters.get("vat_value")) == vat_value[0][0]:
								supplier_name = purchase_invoice[0][0]
								bill_date = purchase_invoice[0][1]
								bill_no = purchase_invoice[0][2]
								supplier_vat_id = purchase_invoice[0][3]
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Supplier",
								supplier_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("from_date") and filters.get("to_date"):
						if gl.posting_date:
							if gl.posting_date >= getdate(filters.from_date) and gl.posting_date <= getdate(filters.to_date) and flt(filters.get("vat_value")) == vat_value[0][0]:
								supplier_name = purchase_invoice[0][0]
								bill_date = purchase_invoice[0][1]
								bill_no = purchase_invoice[0][2]
								supplier_vat_id = purchase_invoice[0][3]
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Supplier",
								supplier_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("account"):
						if filters.get("account") == gl.account and flt(filters.get("vat_value")) == vat_value[0][0]:
							supplier_name = purchase_invoice[0][0]
							bill_date = purchase_invoice[0][1]
							bill_no = purchase_invoice[0][2]
							supplier_vat_id = purchase_invoice[0][3]
							description= pi_desc[0][0]
							row = [
							gl.posting_date,
							vat_value[0][0],
							bill_date,
							gl.account,
							gl.debit,
							gl.credit,
							gl.voucher_type,
							gl.voucher_no,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

					else:
						if flt(filters.get("vat_value")) == vat_value[0][0]:
							supplier_name = purchase_invoice[0][0]
							bill_date = purchase_invoice[0][1]
							bill_no = purchase_invoice[0][2]
							supplier_vat_id = purchase_invoice[0][3]
							description= pi_desc[0][0]
							row = [
							gl.posting_date,
							vat_value[0][0],
							bill_date,
							gl.account,
							gl.debit,
							gl.credit,
							gl.voucher_type,
							gl.voucher_no,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)
				else:
					if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
						if gl.posting_date:
							if gl.posting_date >= getdate(filters.from_date) and gl.posting_date <= getdate(filters.to_date) and filters.get("account") == gl.account:
								supplier_name = purchase_invoice[0][0]
								bill_date = purchase_invoice[0][1]
								bill_no = purchase_invoice[0][2]
								supplier_vat_id = purchase_invoice[0][3]
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Supplier",
								supplier_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("from_date") and filters.get("to_date"):
						if gl.posting_date:
							if gl.posting_date >= getdate(filters.from_date) and gl.posting_date <= getdate(filters.to_date):
								supplier_name = purchase_invoice[0][0]
								bill_date = purchase_invoice[0][1]
								bill_no = purchase_invoice[0][2]
								supplier_vat_id = purchase_invoice[0][3]
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Supplier",
								supplier_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("account"):
						if filters.get("account") == gl.account:
							supplier_name = purchase_invoice[0][0]
							bill_date = purchase_invoice[0][1]
							bill_no = purchase_invoice[0][2]
							supplier_vat_id = purchase_invoice[0][3]
							description= pi_desc[0][0]
							row = [
							gl.posting_date,
							vat_value[0][0],
							bill_date,
							gl.account,
							gl.debit,
							gl.credit,
							gl.voucher_type,
							gl.voucher_no,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

					else:
						supplier_name = purchase_invoice[0][0]
						bill_date = purchase_invoice[0][1]
						bill_no = purchase_invoice[0][2]
						supplier_vat_id = purchase_invoice[0][3]
						description= pi_desc[0][0]
						row = [
						gl.posting_date,
						vat_value[0][0],
						bill_date,
						gl.account,
						gl.debit,
						gl.credit,
						gl.voucher_type,
						gl.voucher_no,
						bill_no,
						"Supplier",
						supplier_name,
						supplier_vat_id,
						description
						]
						data.append(row)
		if gl.voucher_type == 'Sales Invoice':
			if not filters.get("filter_by_supplier"):
				sales_invoice = frappe.db.sql("select customer_name from `tabSales Invoice` where name='{0}' ".format(gl.voucher_no))
				pi_desc = frappe.db.sql ("select description from `tabSales Taxes and Charges` where parent ='{0}'".format(gl.voucher_no))
				vat_value = frappe.db.sql ("select vat from `tabProject Payment Schedule` where parent ='{0}'".format(gl.voucher_no))
				if len(vat_value) == 0:
					vat_value = frappe.db.sql ("select rate from `tabSales Taxes and Charges` where parent ='{0}'".format(gl.voucher_no))
				if filters.get("vat_value"):
					if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
						if gl.posting_date:
							if gl.posting_date >= getdate(filters.from_date) and gl.posting_date <= getdate(filters.to_date) and filters.get("account") == gl.account and flt(filters.get("vat_value")) == vat_value[0][0]:
								customer_name = sales_invoice[0][0]
								bill_date = ""
								bill_no = ""
								supplier_vat_id = ""
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Customer",
								customer_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("from_date") and filters.get("to_date"):
						if gl.posting_date:
							if gl.posting_date >= getdate(filters.from_date) and gl.posting_date <= getdate(filters.to_date) and flt(filters.get("vat_value")) == vat_value[0][0]:
								customer_name = sales_invoice[0][0]
								bill_date = ""
								bill_no = ""
								supplier_vat_id = ""
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Customer",
								customer_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("account"):
						if filters.get("account") == gl.account and flt(filters.get("vat_value")) == vat_value[0][0]:
							customer_name = sales_invoice[0][0]
							bill_date = ""
							bill_no = ""
							supplier_vat_id = ""
							description= pi_desc[0][0]
							row = [
							gl.posting_date,
							vat_value[0][0],
							bill_date,
							gl.account,
							gl.debit,
							gl.credit,
							gl.voucher_type,
							gl.voucher_no,
							bill_no,
							"Customer",
							customer_name,
							supplier_vat_id,
							description
							]
							data.append(row)

					else:
						if flt(filters.get("vat_value")) == vat_value[0][0]:
							customer_name = sales_invoice[0][0]
							bill_date = ""
							bill_no = ""
							supplier_vat_id = ""
							description= pi_desc[0][0]
							row = [
							gl.posting_date,
							vat_value[0][0],
							bill_date,
							gl.account,
							gl.debit,
							gl.credit,
							gl.voucher_type,
							gl.voucher_no,
							bill_no,
							"Customer",
							customer_name,
							supplier_vat_id,
							description
							]
							data.append(row)
				else:
					if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
						if gl.posting_date:
							if gl.posting_date >= getdate(filters.from_date) and gl.posting_date <= getdate(filters.to_date) and filters.get("account") == gl.account:
								customer_name = sales_invoice[0][0]
								bill_date = ""
								bill_no = ""
								supplier_vat_id = ""
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Customer",
								customer_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("from_date") and filters.get("to_date"):
						if gl.posting_date:
							if gl.posting_date >= getdate(filters.from_date) and gl.posting_date <= getdate(filters.to_date):
								customer_name = sales_invoice[0][0]
								bill_date = ""
								bill_no = ""
								supplier_vat_id = ""
								description= pi_desc[0][0]
								row = [
								gl.posting_date,
								vat_value[0][0],
								bill_date,
								gl.account,
								gl.debit,
								gl.credit,
								gl.voucher_type,
								gl.voucher_no,
								bill_no,
								"Customer",
								customer_name,
								supplier_vat_id,
								description
								]
								data.append(row)

					elif filters.get("account"):
						if filters.get("account") == gl.account:
							customer_name = sales_invoice[0][0]
							bill_date = ""
							bill_no = ""
							supplier_vat_id = ""
							description= pi_desc[0][0]
							row = [
							gl.posting_date,
							vat_value[0][0],
							bill_date,
							gl.account,
							gl.debit,
							gl.credit,
							gl.voucher_type,
							gl.voucher_no,
							bill_no,
							"Customer",
							customer_name,
							supplier_vat_id,
							description
							]
							data.append(row)

					else:
						customer_name = sales_invoice[0][0]
						bill_date = ""
						bill_no = ""
						supplier_vat_id = ""
						description= pi_desc[0][0]
						row = [
						gl.posting_date,
						vat_value[0][0],
						bill_date,
						gl.account,
						gl.debit,
						gl.credit,
						gl.voucher_type,
						gl.voucher_no,
						bill_no,
						"Customer",
						customer_name,
						supplier_vat_id,
						description
						]
						data.append(row)
	# return data

	# gl_list_je=frappe.db.sql(""" select name,posting_date,account,debit,credit,voucher_type,voucher_no,description from `tabGL Entry` where (voucher_type='Journal Entry') and (account='22290001-RECEIVABLE VAT -ضريبة قيمة مضافة قابلة للخصم - T' or account='22290002-PAYABLE VAT - ضريبة قيمة مضافة مستحقة -T - T') order by posting_date asc""",as_dict=1)
	# for gl in gl_list_je:
	# if gl.voucher_type == 'Journal Entry':
	je_list = frappe.db.sql ("select `tabJournal Entry Account`.account,`tabJournal Entry Account`.debit,`tabJournal Entry Account`.credit,`tabJournal Entry`.voucher_type,`tabJournal Entry`.posting_date,`tabJournal Entry`.name,`tabJournal Entry Account`.supplier,`tabJournal Entry Account`.supplier_invoice_date,`tabJournal Entry Account`.supplier_invoice_no,`tabJournal Entry Account`.supplier_vat_id,`tabJournal Entry Account`.vat_value2,`tabJournal Entry Account`.description from `tabJournal Entry Account` INNER JOIN `tabJournal Entry` ON `tabJournal Entry`.name=`tabJournal Entry Account`.parent where (`tabJournal Entry Account`.account='22290001-RECEIVABLE VAT -ضريبة قيمة مضافة قابلة للخصم - T 15% - T' or `tabJournal Entry Account`.account='22290001-RECEIVABLE VAT -ضريبة قيمة مضافة قابلة للخصم - T 5% - T' or `tabJournal Entry Account`.account='22290002-PAYABLE VAT - ضريبة قيمة مضافة مستحقة -T - 15% - T'or `tabJournal Entry Account`.account='22290002-PAYABLE VAT - ضريبة قيمة مضافة مستحقة -T - 5%  - T') order by `tabJournal Entry`.posting_date asc ",as_dict=1)
	vat_value = ""
	# je_account = frappe.db.sql("select supplier,supplier_invoice_date,supplier_invoice_no,supplier_vat_id,description,account,debit,credit,parent from `tabJournal Entry Account` where (account='22290001-RECEIVABLE VAT -ضريبة قيمة مضافة قابلة للخصم - T' or account='22290002-PAYABLE VAT - ضريبة قيمة مضافة مستحقة -T - T') ",as_dict=1)
	for je in je_list:
		if je.supplier :
			supplier_doc = frappe.get_doc("Supplier",je.supplier)
			supplier_name =supplier_doc.supplier_name
		else :
			supplier_name =''
		if filters.get("filter_by_supplier"):
			if filters.get("vat_value"):
				if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
					if je.supplier_invoice_date:
						if je.supplier_invoice_date >= getdate(filters.from_date) and je.supplier_invoice_date <= getdate(filters.to_date) and filters.get("account") == je.account and filters.get("vat_value") == je.vat_value2:
							bill_date = je.supplier_invoice_date
							bill_no = je.supplier_invoice_no
							# supplier_name = je.supplier
							supplier_vat_id = je.supplier_vat_id
							description = je.description

							row = [
							je.posting_date,
							je.vat_value2,
							bill_date,
							je.account,
							je.debit,
							je.credit,
							je.voucher_type,
							je.name,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

				elif filters.get("from_date") and filters.get("to_date"):
					if je.supplier_invoice_date:
						if je.supplier_invoice_date >= getdate(filters.from_date) and je.supplier_invoice_date <= getdate(filters.to_date) and filters.get("vat_value") == je.vat_value2:
							bill_date = je.supplier_invoice_date
							bill_no = je.supplier_invoice_no
							# supplier_name = je.supplier
							supplier_vat_id = je.supplier_vat_id
							description = je.description

							row = [
							je.posting_date,
							je.vat_value2,
							bill_date,
							je.account,
							je.debit,
							je.credit,
							je.voucher_type,
							je.name,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

				elif filters.get("account"):
					if filters.get("account") == je.account and filters.get("vat_value") == je.vat_value2:
						bill_date = je.supplier_invoice_date
						bill_no = je.supplier_invoice_no
						# supplier_name = je.supplier
						supplier_vat_id = je.supplier_vat_id
						description = je.description

						row = [
						je.posting_date,
						je.vat_value2,
						bill_date,
						je.account,
						je.debit,
						je.credit,
						je.voucher_type,
						je.name,
						bill_no,
						"Supplier",
						supplier_name,
						supplier_vat_id,
						description
						]
						data.append(row)

				else:
					if filters.get("vat_value") == je.vat_value2:
						bill_date = je.supplier_invoice_date
						bill_no = je.supplier_invoice_no
						# supplier_name = je.supplier
						supplier_vat_id = je.supplier_vat_id
						description = je.description
						row = [
						je.posting_date,
						je.vat_value2,
						bill_date,
						je.account,
						je.debit,
						je.credit,
						je.voucher_type,
						je.name,
						bill_no,
						"Supplier",
						supplier_name,
						supplier_vat_id,
						description
						]
						data.append(row)
			else:
				if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
					if je.supplier_invoice_date:
						if je.supplier_invoice_date >= getdate(filters.from_date) and je.supplier_invoice_date <= getdate(filters.to_date) and filters.get("account") == je.account:
							bill_date = je.supplier_invoice_date
							bill_no = je.supplier_invoice_no
							# supplier_name = je.supplier
							supplier_vat_id = je.supplier_vat_id
							description = je.description

							row = [
							je.posting_date,
							je.vat_value2,
							bill_date,
							je.account,
							je.debit,
							je.credit,
							je.voucher_type,
							je.name,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

				elif filters.get("from_date") and filters.get("to_date"):
					if je.supplier_invoice_date:
						if je.supplier_invoice_date >= getdate(filters.from_date) and je.supplier_invoice_date <= getdate(filters.to_date):
							bill_date = je.supplier_invoice_date
							bill_no = je.supplier_invoice_no
							# supplier_name = je.supplier
							supplier_vat_id = je.supplier_vat_id
							description = je.description

							row = [
							je.posting_date,
							je.vat_value2,
							bill_date,
							je.account,
							je.debit,
							je.credit,
							je.voucher_type,
							je.name,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

				elif filters.get("account"):
					if filters.get("account") == je.account:
						bill_date = je.supplier_invoice_date
						bill_no = je.supplier_invoice_no
						# supplier_name = je.supplier
						supplier_vat_id = je.supplier_vat_id
						description = je.description

						row = [
						je.posting_date,
						je.vat_value2,
						bill_date,
						je.account,
						je.debit,
						je.credit,
						je.voucher_type,
						je.name,
						bill_no,
						"Supplier",
						supplier_name,
						supplier_vat_id,
						description
						]
						data.append(row)

				else:
					bill_date = je.supplier_invoice_date
					bill_no = je.supplier_invoice_no
					# supplier_name = je.supplier
					supplier_vat_id = je.supplier_vat_id
					description = je.description
					row = [
					je.posting_date,
					je.vat_value2,
					bill_date,
					je.account,
					je.debit,
					je.credit,
					je.voucher_type,
					je.name,
					bill_no,
					"Supplier",
					supplier_name,
					supplier_vat_id,
					description
					]
					data.append(row)
		else:
			if filters.get("vat_value"):
				if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
					if je.posting_date:
						if je.posting_date >= getdate(filters.from_date) and je.posting_date <= getdate(filters.to_date) and filters.get("account") == je.account and filters.get("vat_value") == je.vat_value2:
							bill_date = je.supplier_invoice_date
							bill_no = je.supplier_invoice_no
							# supplier_name = je.supplier
							supplier_vat_id = je.supplier_vat_id
							description = je.description

							row = [
							je.posting_date,
							je.vat_value2,
							bill_date,
							je.account,
							je.debit,
							je.credit,
							je.voucher_type,
							je.name,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

				elif filters.get("from_date") and filters.get("to_date"):
					if je.posting_date:
						if je.posting_date >= getdate(filters.from_date) and je.posting_date <= getdate(filters.to_date) and filters.get("vat_value") == je.vat_value2:
							bill_date = je.supplier_invoice_date
							bill_no = je.supplier_invoice_no
							# supplier_name = je.supplier
							supplier_vat_id = je.supplier_vat_id
							description = je.description

							row = [
							je.posting_date,
							je.vat_value2,
							bill_date,
							je.account,
							je.debit,
							je.credit,
							je.voucher_type,
							je.name,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

				elif filters.get("account"):
					if filters.get("account") == je.account and filters.get("vat_value") == je.vat_value2:
						bill_date = je.supplier_invoice_date
						bill_no = je.supplier_invoice_no
						# supplier_name = je.supplier
						supplier_vat_id = je.supplier_vat_id
						description = je.description

						row = [
						je.posting_date,
						je.vat_value2,
						bill_date,
						je.account,
						je.debit,
						je.credit,
						je.voucher_type,
						je.name,
						bill_no,
						"Supplier",
						supplier_name,
						supplier_vat_id,
						description
						]
						data.append(row)

				else:
					if filters.get("vat_value") == je.vat_value2 :
						bill_date = je.supplier_invoice_date
						bill_no = je.supplier_invoice_no
						# supplier_name = je.supplier
						supplier_vat_id = je.supplier_vat_id
						description = je.description
						row = [
						je.posting_date,
						je.vat_value2,
						bill_date,
						je.account,
						je.debit,
						je.credit,
						je.voucher_type,
						je.name,
						bill_no,
						"Supplier",
						supplier_name,
						supplier_vat_id,
						description
						]
						data.append(row)
			else:
				if filters.get("from_date") and filters.get("to_date") and filters.get("account"):
					if je.posting_date:
						if je.posting_date >= getdate(filters.from_date) and je.posting_date <= getdate(filters.to_date) and filters.get("account") == je.account:
							bill_date = je.supplier_invoice_date
							bill_no = je.supplier_invoice_no
							# supplier_name = je.supplier
							supplier_vat_id = je.supplier_vat_id
							description = je.description

							row = [
							je.posting_date,
							je.vat_value2,
							bill_date,
							je.account,
							je.debit,
							je.credit,
							je.voucher_type,
							je.name,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

				elif filters.get("from_date") and filters.get("to_date"):
					if je.posting_date:
						if je.posting_date >= getdate(filters.from_date) and je.posting_date <= getdate(filters.to_date):
							bill_date = je.supplier_invoice_date
							bill_no = je.supplier_invoice_no
							# supplier_name = je.supplier
							supplier_vat_id = je.supplier_vat_id
							description = je.description

							row = [
							je.posting_date,
							je.vat_value2,
							bill_date,
							je.account,
							je.debit,
							je.credit,
							je.voucher_type,
							je.name,
							bill_no,
							"Supplier",
							supplier_name,
							supplier_vat_id,
							description
							]
							data.append(row)

				elif filters.get("account"):
					if filters.get("account") == je.account:
						bill_date = je.supplier_invoice_date
						bill_no = je.supplier_invoice_no
						# supplier_name = je.supplier
						supplier_vat_id = je.supplier_vat_id
						description = je.description

						row = [
						je.posting_date,
						je.vat_value2,
						bill_date,
						je.account,
						je.debit,
						je.credit,
						je.voucher_type,
						je.name,
						bill_no,
						"Supplier",
						supplier_name,
						supplier_vat_id,
						description
						]
						data.append(row)

				else:
					bill_date = je.supplier_invoice_date
					bill_no = je.supplier_invoice_no
					# supplier_name = je.supplier
					supplier_vat_id = je.supplier_vat_id
					description = je.description
					row = [
					je.posting_date,
					je.vat_value2,
					bill_date,
					je.account,
					je.debit,
					je.credit,
					je.voucher_type,
					je.name,
					bill_no,
					"Supplier",
					supplier_name,
					supplier_vat_id,
					description
					]
					data.append(row)

	# return data


	return data
