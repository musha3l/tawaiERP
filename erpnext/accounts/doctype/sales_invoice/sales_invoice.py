# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import frappe.defaults
from frappe.utils import cint, flt
from frappe import _, msgprint, throw
from erpnext.accounts.party import get_party_account, get_due_date
from erpnext.controllers.stock_controller import update_gl_entries_after
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.doctype.sales_invoice.pos import update_multi_mode_option

from erpnext.controllers.selling_controller import SellingController
from erpnext.accounts.utils import get_account_currency
from erpnext.stock.doctype.delivery_note.delivery_note import update_billed_amount_based_on_so
from erpnext.projects.doctype.timesheet.timesheet import get_projectwise_timesheet_data
from erpnext.accounts.doctype.asset.depreciation \
    import get_disposal_account_and_cost_center, get_gl_entries_on_asset_disposal

form_grid_templates = {
    "items": "templates/form_grid/item_grid.html"
}

class SalesInvoice(SellingController):
    def __init__(self, arg1, arg2=None):
        super(SalesInvoice, self).__init__(arg1, arg2)
        self.status_updater = [{
            'source_dt': 'Sales Invoice Item',
            'target_field': 'billed_amt',
            'target_ref_field': 'amount',
            'target_dt': 'Sales Order Item',
            'join_field': 'so_detail',
            'target_parent_dt': 'Sales Order',
            'target_parent_field': 'per_billed',
            'source_field': 'amount',
            'join_field': 'so_detail',
            'percent_join_field': 'sales_order',
            'status_field': 'billing_status',
            'keyword': 'Billed',
            'overflow_type': 'billing'
        }]

    def set_indicator(self):
        """Set indicator for portal"""
        if self.outstanding_amount > 0:
            self.indicator_color = "orange"
            self.indicator_title = _("Unpaid")
        else:
            self.indicator_color = "green"
            self.indicator_title = _("Paid")

    def validate(self):

        super(SalesInvoice, self).validate()
        self.validate_posting_time()
        # self.so_dn_required()
        self.validate_proj_cust()
        self.validate_with_previous_doc()
        self.validate_uom_is_integer("stock_uom", "qty")
        self.check_close_sales_order("sales_order")
        self.validate_debit_to_acc()
        self.clear_unallocated_advances("Sales Invoice Advance", "advances")
        self.add_remarks()
        self.validate_write_off_account()
        self.validate_account_for_change_amount()
        self.validate_fixed_asset()
        self.set_income_account_for_fixed_assets()
        # self.calculate_total_paid_advance()
        self.calculate_total_billing_value()


        if cint(self.is_pos):
            self.validate_pos()

        if cint(self.update_stock):
            self.validate_dropship_item()
            self.validate_item_code()
            self.validate_warehouse()
            self.update_current_stock()
            self.validate_delivery_note()

        if not self.is_opening:
            self.is_opening = 'No'

        self.set_against_income_account()
        self.validate_c_form()
        self.validate_time_sheets_are_submitted()
        self.validate_multiple_billing("Delivery Note", "dn_detail", "amount", "items")
        self.update_packing_list()
        self.set_billing_hours_and_amount()
        self.update_timesheet_billing_for_project()
        self.set_status()
        if self.get("__islocal") :
                self.title = self.get_title()
        self.set_items_income_account()


        self.validate_emp()
        self.validate_project_item_advance()

        if self.workflow_state:
            if "Rejected" in self.workflow_state:
                self.docstatus = 1
                self.docstatus = 2


    def validate_emp(self):
        if self.get('__islocal'):
            if u'Finance MGR' in frappe.get_roles(frappe.session.user):
                self.workflow_state = "Pending"
            else :
                self.workflow_state = "Pending"


    def calculate_total_paid_advance(self):
        advance_total = 0
        advanced = frappe.db.sql_list("select distinct advance_project_items from `tabProject Payment Schedule` where parent='{0}'".format(self.project))
        for item in self.project_payment_schedule_invoice:
            if item.scope_item in advanced:
                frappe.msgprint(str(item.billing_value))
                advance_amount = flt(item.billing_value) * flt(flt(item.billing_percentage)/100)
                advance_tax = flt(advance_amount) * flt(flt(item.vat)/100)
                total = advance_amount + advance_tax

                advance_total = advance_total + total
        self.total_advance = advance_total
        self.item_advance_amount = advance_total


    def calculate_total_billing_value(self):
        if self.project_payment_schedule_invoice:
            for item in self.project_payment_schedule_invoice:
                self.total_billing_value = item.total_billing_value


    def validate_project_item_advance(self):
        # if self.get('__islocal'):
        self.total_demand = self.grand_total-flt(self.item_advance_amount)



    def get_title(self):
        from frappe.utils import getdate

        namming =frappe.get_list("Enhanced Nameing Doc", fields=["name","name_of_doc", "index_value","year"],filters={"year": str(getdate(self.posting_date).year),"name_of_doc":self.doctype},ignore_permissions=True)
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
            nammeing_doc.parentfield='enhanced_nameing'
            nammeing_doc.naming_series = self.naming_series
            nammeing_doc.index_value = 1
            nammeing_doc.year = str(getdate(self.posting_date).year)
            nammeing_doc.name_of_doc = self.doctype
            nammeing_doc.save(ignore_permissions=True)
            return title

    def set_items_income_account(self):
        #~ if self.get("__islocal"):
        customer_group = frappe.db.get_value("Customer", self.customer, "customer_group")
        if customer_group:
            customer_group_income_account = frappe.db.get_value("Customer Group", self.customer_group, "default_income_account")

            if customer_group_income_account :
                for item in self.get("items"):
                    if frappe.db.get_value("Item", item.item_code, "is_advance_item") == 0:
                        if not (self.workflow_state =='Reviewed By Accounts Manager' or self.workflow_state =='Approved By Finance MGR'):
                            item.income_account=customer_group_income_account
        #~ if self.get("payment_schedule") :
            #~ payment_schedule = self.get("payment_schedule")
            #~ for pt in payment_schedule :

                #~ if pt.is_advance == 1 and pt.payment_term == self.payment_term:
                    #~ for item in self.get("items"):
                        #~ item.income_account=pt.account

                #~ if pt.is_retention == 1 and pt.payment_term == self.payment_term:
                    #~ for item in self.get("items"):
                        #~ item.income_account=pt.account


    def get_payment_units_share(self):
        if self.payment_term_unit :
            p_options= frappe.get_doc("Payment Term Unit",{"name":self.payment_term_unit})
            return p_options.payment_percentage
        else:
            return 0.0

    def get_payment_units(self):
        if self.payment_terms :
            p_options= frappe.get_list("Payment Term Unit", fields=["Term", "name"], filters={"parent":self.payment_terms})
            return p_options
        else:
            return {}
    def before_save(self):
        set_account_for_mode_of_payment(self)

    def on_submit(self):
        self.validate_pos_paid_amount()

        if not self.recurring_id:
            frappe.get_doc('Authorization Control').validate_approving_authority(self.doctype,
                self.company, self.base_grand_total, self)

        self.check_prev_docstatus()

        if self.is_return:
            # NOTE status updating bypassed for is_return
            self.status_updater = []

        self.update_status_updater_args()
        self.update_prevdoc_status()
        self.update_billing_status_in_dn()
        self.clear_unallocated_mode_of_payments()

        # Updating stock ledger should always be called after updating prevdoc status,
        # because updating reserved qty in bin depends upon updated delivered qty in SO
        if self.update_stock == 1:
            self.update_stock_ledger()

        # this sequence because outstanding may get -ve
        self.make_gl_entries()

        if not self.is_return:
            self.update_billing_status_for_zero_amount_refdoc("Sales Order")
            self.check_credit_limit()

        if not cint(self.is_pos) == 1 and not self.is_return:
            self.update_against_document_in_jv()

        self.update_time_sheet(self.name)

    def validate_pos_paid_amount(self):
        if len(self.payments) == 0 and self.is_pos:
            frappe.throw(_("At least one mode of payment is required for POS invoice."))

    def before_cancel(self):
        self.update_time_sheet(None)

    def on_cancel(self):
        self.check_close_sales_order("sales_order")

        from erpnext.accounts.utils import unlink_ref_doc_from_payment_entries
        if frappe.db.get_single_value('Accounts Settings', 'unlink_payment_on_cancellation_of_invoice'):
            unlink_ref_doc_from_payment_entries(self)

        if self.is_return:
            # NOTE status updating bypassed for is_return
            self.status_updater = []

        self.update_status_updater_args()
        self.update_prevdoc_status()
        self.update_billing_status_in_dn()

        if not self.is_return:
            self.update_billing_status_for_zero_amount_refdoc("Sales Order")

        self.validate_c_form_on_cancel()

        # Updating stock ledger should always be called after updating prevdoc status,
        # because updating reserved qty in bin depends upon updated delivered qty in SO
        if self.update_stock == 1:
            self.update_stock_ledger()

        self.make_gl_entries_on_cancel()
        frappe.db.set(self, 'status', 'Cancelled')

    def update_status_updater_args(self):
        if cint(self.update_stock):
            self.status_updater.extend([{
                'source_dt':'Sales Invoice Item',
                'target_dt':'Sales Order Item',
                'target_parent_dt':'Sales Order',
                'target_parent_field':'per_delivered',
                'target_field':'delivered_qty',
                'target_ref_field':'qty',
                'source_field':'qty',
                'join_field':'so_detail',
                'percent_join_field':'sales_order',
                'status_field':'delivery_status',
                'keyword':'Delivered',
                'second_source_dt': 'Delivery Note Item',
                'second_source_field': 'qty',
                'second_join_field': 'so_detail',
                'overflow_type': 'delivery',
                'extra_cond': """ and exists(select name from `tabSales Invoice`
                    where name=`tabSales Invoice Item`.parent and update_stock = 1)"""
            },
            {
                'source_dt': 'Sales Invoice Item',
                'target_dt': 'Sales Order Item',
                'join_field': 'so_detail',
                'target_field': 'returned_qty',
                'target_parent_dt': 'Sales Order',
                # 'target_parent_field': 'per_delivered',
                # 'target_ref_field': 'qty',
                'source_field': '-1 * qty',
                # 'percent_join_field': 'sales_order',
                # 'overflow_type': 'delivery',
                'extra_cond': """ and exists (select name from `tabSales Invoice` where name=`tabSales Invoice Item`.parent and update_stock=1 and is_return=1)"""
            }
        ])

    def check_credit_limit(self):
        from erpnext.selling.doctype.customer.customer import check_credit_limit

        validate_against_credit_limit = False
        for d in self.get("items"):
            if not (d.sales_order or d.delivery_note):
                validate_against_credit_limit = True
                break
        if validate_against_credit_limit:
            check_credit_limit(self.customer, self.company)

    def set_missing_values(self, for_validate=False):
        pos = self.set_pos_fields(for_validate)

        if not self.debit_to:
            self.debit_to = get_party_account("Customer", self.customer, self.company)
        if not self.due_date and self.customer:
            self.due_date = get_due_date(self.posting_date, "Customer", self.customer, self.company)

        super(SalesInvoice, self).set_missing_values(for_validate)

        if pos:
            return {"print_format": pos.get("print_format") }

    def update_time_sheet(self, sales_invoice):
        for d in self.timesheets:
            if d.time_sheet:
                timesheet = frappe.get_doc("Timesheet", d.time_sheet)
                self.update_time_sheet_detail(timesheet, d, sales_invoice)
                timesheet.calculate_total_amounts()
                timesheet.calculate_percentage_billed()
                timesheet.flags.ignore_validate_update_after_submit = True
                timesheet.set_status()
                timesheet.save()

    def update_time_sheet_detail(self, timesheet, args, sales_invoice):
        for data in timesheet.time_logs:
            if (self.project and args.timesheet_detail == data.name) or \
                (not self.project and not data.sales_invoice) or \
                (not sales_invoice and data.sales_invoice == self.name):
                data.sales_invoice = sales_invoice
                if self.project: return

    def on_update(self):
        self.set_paid_amount()

    def set_paid_amount(self):
        paid_amount = 0.0
        base_paid_amount = 0.0
        for data in self.payments:
            data.base_amount = flt(data.amount*self.conversion_rate, self.precision("base_paid_amount"))
            paid_amount += data.amount
            base_paid_amount += data.base_amount

        self.paid_amount = paid_amount
        self.base_paid_amount = base_paid_amount

    def validate_time_sheets_are_submitted(self):
        for data in self.timesheets:
            if data.time_sheet:
                status = frappe.db.get_value("Timesheet", data.time_sheet, "status")
                if status not in ['Submitted', 'Payslip']:
                    frappe.throw(_("Timesheet {0} is already completed or cancelled").format(data.time_sheet))

    def set_pos_fields(self, for_validate=False):
        """Set retail related fields from POS Profiles"""
        if cint(self.is_pos) != 1:
            return

        from erpnext.stock.get_item_details import get_pos_profile_item_details, get_pos_profile
        pos = get_pos_profile(self.company)

        if not self.get('payments') and not for_validate:
            pos_profile = frappe.get_doc('POS Profile', pos.name) if pos else None
            update_multi_mode_option(self, pos_profile)

        if not self.account_for_change_amount:
            self.account_for_change_amount = frappe.db.get_value('Company', self.company, 'default_cash_account')

        if pos:
            if not for_validate and not self.customer:
                self.customer = pos.customer
                self.mode_of_payment = pos.mode_of_payment
                # self.set_customer_defaults()

            if pos.get('account_for_change_amount'):
                self.account_for_change_amount = pos.get('account_for_change_amount')

            for fieldname in ('territory', 'naming_series', 'currency', 'taxes_and_charges', 'letter_head', 'tc_name',
                'selling_price_list', 'company', 'select_print_heading', 'cash_bank_account',
                'write_off_account', 'write_off_cost_center'):
                    if (not for_validate) or (for_validate and not self.get(fieldname)):
                        self.set(fieldname, pos.get(fieldname))

            if not for_validate:
                self.update_stock = cint(pos.get("update_stock"))

            # set pos values in items
            for item in self.get("items"):
                if item.get('item_code'):
                    for fname, val in get_pos_profile_item_details(pos,
                        frappe._dict(item.as_dict()), pos).items():

                        if (not for_validate) or (for_validate and not item.get(fname)):
                            item.set(fname, val)

            # fetch terms
            if self.tc_name and not self.terms:
                self.terms = frappe.db.get_value("Terms and Conditions", self.tc_name, "terms")

            # fetch charges
            if self.taxes_and_charges and not len(self.get("taxes")):
                self.set_taxes()

        return pos

    def get_company_abbr(self):
        return frappe.db.sql("select abbr from tabCompany where name=%s", self.company)[0][0]

    def validate_debit_to_acc(self):
        account = frappe.db.get_value("Account", self.debit_to,
            ["account_type", "report_type", "account_currency"], as_dict=True)

        if not account:
            frappe.throw(_("Debit To is required"))

        if account.report_type != "Balance Sheet":
            frappe.throw(_("Debit To account must be a Balance Sheet account"))

        if self.customer and account.account_type != "Receivable":
            frappe.throw(_("Debit To account must be a Receivable account"))

        self.party_account_currency = account.account_currency

    def clear_unallocated_mode_of_payments(self):
        self.set("payments", self.get("payments", {"amount": ["not in", [0, None, ""]]}))

        frappe.db.sql("""delete from `tabSales Invoice Payment` where parent = %s
            and amount = 0""", self.name)

    def validate_with_previous_doc(self):
        super(SalesInvoice, self).validate_with_previous_doc({
            "Sales Order": {
                "ref_dn_field": "sales_order",
                "compare_fields": [["customer", "="], ["company", "="], ["project", "="],
                    ["currency", "="]],
            },
            "Delivery Note": {
                "ref_dn_field": "delivery_note",
                "compare_fields": [["customer", "="], ["company", "="], ["project", "="],
                    ["currency", "="]],
            },
        })

        if cint(frappe.db.get_single_value('Selling Settings', 'maintain_same_sales_rate')) and not self.is_return:
            self.validate_rate_with_reference_doc([
                ["Sales Order", "sales_order", "so_detail"],
                ["Delivery Note", "delivery_note", "dn_detail"]
            ])

    def set_against_income_account(self):
        """Set against account for debit to account"""
        against_acc = []
        for d in self.get('items'):
            if d.income_account and d.income_account not in against_acc:
                against_acc.append(d.income_account)
        self.against_income_account = ','.join(against_acc)

    def add_remarks(self):
        if not self.remarks: self.remarks = 'No Remarks'


    def so_dn_required(self):
        """check in manage account if sales order / delivery note required or not."""
        dic = {'Sales Order':['so_required', 'is_pos'],'Delivery Note':['dn_required', 'update_stock']}
        for i in dic:
            if frappe.db.get_value('Selling Settings', None, dic[i][0]) == 'Yes':
                for d in self.get('items'):
                    if frappe.db.get_value('Item', d.item_code, 'is_stock_item') == 1 \
                        and not d.get(i.lower().replace(' ','_')) and not self.get(dic[i][1]):
                        msgprint(_("{0} is mandatory for Item {1}").format(i,d.item_code), raise_exception=1)


    def validate_proj_cust(self):
        """check for does customer belong to same project as entered.."""
        if self.project and self.customer:
            res = frappe.db.sql("""select name from `tabProject`
                where name = %s and (customer = %s or customer is null or customer = '')""",
                (self.project, self.customer))
            if not res:
                throw(_("Customer {0} does not belong to project {1}").format(self.customer,self.project))

    def validate_pos(self):
        if flt(self.paid_amount) + flt(self.write_off_amount) \
                - flt(self.grand_total) > 1/(10**(self.precision("grand_total") + 1)) and self.is_return:
            frappe.throw(_("""Paid amount + Write Off Amount can not be greater than Grand Total"""))


    def validate_item_code(self):
        for d in self.get('items'):
            if not d.item_code:
                msgprint(_("Item Code required at Row No {0}").format(d.idx), raise_exception=True)

    def validate_warehouse(self):
        super(SalesInvoice, self).validate_warehouse()

        for d in self.get_item_list():
            if not d.warehouse and frappe.db.get_value("Item", d.item_code, "is_stock_item"):
                frappe.throw(_("Warehouse required for stock Item {0}").format(d.item_code))

    def validate_delivery_note(self):
        for d in self.get("items"):
            if d.delivery_note:
                msgprint(_("Stock cannot be updated against Delivery Note {0}").format(d.delivery_note), raise_exception=1)

    def validate_write_off_account(self):
        if flt(self.write_off_amount) and not self.write_off_account:
            self.write_off_account = frappe.db.get_value('Company', self.company, 'write_off_account')

        if flt(self.write_off_amount) and not self.write_off_account:
            msgprint(_("Please enter Write Off Account"), raise_exception=1)

    def validate_account_for_change_amount(self):
        if flt(self.change_amount) and not self.account_for_change_amount:
            msgprint(_("Please enter Account for Change Amount"), raise_exception=1)

    def validate_c_form(self):
        """ Blank C-form no if C-form applicable marked as 'No'"""
        if self.amended_from and self.c_form_applicable == 'No' and self.c_form_no:
            frappe.db.sql("""delete from `tabC-Form Invoice Detail` where invoice_no = %s
                    and parent = %s""", (self.amended_from, self.c_form_no))

            frappe.db.set(self, 'c_form_no', '')

    def validate_c_form_on_cancel(self):
        """ Display message if C-Form no exists on cancellation of Sales Invoice"""
        if self.c_form_applicable == 'Yes' and self.c_form_no:
            msgprint(_("Please remove this Invoice {0} from C-Form {1}")
                .format(self.name, self.c_form_no), raise_exception = 1)

    def validate_dropship_item(self):
        for item in self.items:
            if item.sales_order:
                if frappe.db.get_value("Sales Order Item", item.so_detail, "delivered_by_supplier"):
                    frappe.throw(_("Could not update stock, invoice contains drop shipping item."))

    def update_current_stock(self):
        for d in self.get('items'):
            if d.item_code and d.warehouse:
                bin = frappe.db.sql("select actual_qty from `tabBin` where item_code = %s and warehouse = %s", (d.item_code, d.warehouse), as_dict = 1)
                d.actual_qty = bin and flt(bin[0]['actual_qty']) or 0

        for d in self.get('packed_items'):
            bin = frappe.db.sql("select actual_qty, projected_qty from `tabBin` where item_code =   %s and warehouse = %s", (d.item_code, d.warehouse), as_dict = 1)
            d.actual_qty = bin and flt(bin[0]['actual_qty']) or 0
            d.projected_qty = bin and flt(bin[0]['projected_qty']) or 0

    def update_packing_list(self):
        if cint(self.update_stock) == 1:
            from erpnext.stock.doctype.packed_item.packed_item import make_packing_list
            make_packing_list(self)
        else:
            self.set('packed_items', [])

    def set_billing_hours_and_amount(self):
        for timesheet in self.timesheets:
            ts_doc = frappe.get_doc('Timesheet', timesheet.time_sheet)
            if not timesheet.billing_hours and ts_doc.total_billable_hours:
                timesheet.billing_hours = ts_doc.total_billable_hours

            if not timesheet.billing_amount and ts_doc.total_billable_amount:
                timesheet.billing_amount = ts_doc.total_billable_amount

    def update_timesheet_billing_for_project(self):
        if not self.timesheets and self.project:
            self.add_timesheet_data()
        else:
            self.calculate_billing_amount_for_timesheet()

    def add_timesheet_data(self):
        self.set('timesheets', [])
        if self.project:
            for data in get_projectwise_timesheet_data(self.project):
                self.append('timesheets', {
                        'time_sheet': data.parent,
                        'billing_hours': data.billing_hours,
                        'billing_amount': data.billing_amt,
                        'timesheet_detail': data.name
                    })

            self.calculate_billing_amount_for_timesheet()

    def calculate_billing_amount_for_timesheet(self):
        total_billing_amount = 0.0
        for data in self.timesheets:
            if data.billing_amount:
                total_billing_amount += data.billing_amount

        self.total_billing_amount = total_billing_amount

    def get_warehouse(self):
        user_pos_profile = frappe.db.sql("""select name, warehouse from `tabPOS Profile`
            where ifnull(user,'') = %s and company = %s""", (frappe.session['user'], self.company))
        warehouse = user_pos_profile[0][1] if user_pos_profile else None

        if not warehouse:
            global_pos_profile = frappe.db.sql("""select name, warehouse from `tabPOS Profile`
                where (user is null or user = '') and company = %s""", self.company)

            if global_pos_profile:
                warehouse = global_pos_profile[0][1]
            elif not user_pos_profile:
                msgprint(_("POS Profile required to make POS Entry"), raise_exception=True)

        return warehouse

    def set_income_account_for_fixed_assets(self):
        disposal_account = depreciation_cost_center = None
        for d in self.get("items"):
            if d.is_fixed_asset:
                if not disposal_account:
                    disposal_account, depreciation_cost_center = get_disposal_account_and_cost_center(self.company)

                d.income_account = disposal_account
                if not d.cost_center:
                    d.cost_center = depreciation_cost_center

    def check_prev_docstatus(self):
        for d in self.get('items'):
            if d.sales_order and frappe.db.get_value("Sales Order", d.sales_order, "docstatus") != 1:
                frappe.throw(_("Sales Order {0} is not submitted").format(d.sales_order))

            if d.delivery_note and frappe.db.get_value("Delivery Note", d.delivery_note, "docstatus") != 1:
                throw(_("Delivery Note {0} is not submitted").format(d.delivery_note))

    def make_gl_entries(self, repost_future_gle=True):
        if not self.grand_total:
            return
        gl_entries = self.get_gl_entries()

        if gl_entries:
            from erpnext.accounts.general_ledger import make_gl_entries

            # if POS and amount is written off, updating outstanding amt after posting all gl entries
            update_outstanding = "No" if (cint(self.is_pos) or self.write_off_account) else "Yes"

            make_gl_entries(gl_entries, cancel=(self.docstatus == 2),
                update_outstanding=update_outstanding, merge_entries=False)

            if update_outstanding == "No":
                from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
                update_outstanding_amt(self.debit_to, "Customer", self.customer,
                    self.doctype, self.return_against if cint(self.is_return) else self.name)

            if repost_future_gle and cint(self.update_stock) \
                and cint(frappe.defaults.get_global_default("auto_accounting_for_stock")):
                    items, warehouses = self.get_items_and_warehouses()
                    update_gl_entries_after(self.posting_date, self.posting_time, warehouses, items)
        elif self.docstatus == 2 and cint(self.update_stock) \
            and cint(frappe.defaults.get_global_default("auto_accounting_for_stock")):
                from erpnext.accounts.general_ledger import delete_gl_entries
                delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

    def get_gl_entries(self, warehouse_account=None):
        from erpnext.accounts.general_ledger import merge_similar_entries

        gl_entries = []

        detail =frappe.get_list("Payment Terms Template Detail",
                fields=["name","is_advance", "apply_tax","is_retention","payment_term"],
                filters={"parent":self.get("payment_terms_template"),"payment_term":self.payment_term},
                ignore_permissions=True)

        status = "All"

        self.make_customer_gl_entry(gl_entries)

        self.make_tax_gl_entries(gl_entries)

        self.make_item_gl_entries(gl_entries)

        # merge gl entries before adding pos entries
        gl_entries = merge_similar_entries(gl_entries)

        self.make_pos_gl_entries(gl_entries)
        self.make_gle_for_change_amount(gl_entries)
        self.make_write_off_gl_entry(gl_entries)

        return gl_entries

    def get_payment_schdual(self):
        res = []
        for item in self.items :
            if item.project_payment_schedule:
                ps_doc = frappe.get_doc("Project Payment Schedule",item.project_payment_schedule)
                adv_ps_list =frappe.get_list("Project Payment Schedule",
                    fields=["name","sales_invoice"],
                    filters={"parent":ps_doc.parent,"advance_project_items  ":ps_doc.scope_item},
                    ignore_permissions=True)

                if adv_ps_list :
                    for i in adv_ps_list:
                        if i.name != ps_doc.name:
                            i.billing_percentage=ps_doc.billing_percentage
                            res.append(i)

        adv_ps_docs = res
        adv_ps_docs = [i for n, i in enumerate(res) if i not in res[n + 1:]]
        print (adv_ps_docs)
        for r in adv_ps_docs :
            if not r.sales_invoice:
                frappe.throw("Make sure that advance invoice is made ")
        return adv_ps_docs


    def make_payment_term_gl_entry(self, gl_entries):
        if self.total :
            # Didnot use base_grand_total to book rounding loss gle
            grand_total_in_company_currency = flt(self.grand_total * self.conversion_rate,
                self.precision("grand_total"))
            invoice_portions_total = 0
            tax_destribution= {}
            advance_invoice_portion = 0
            retention_invoice_portion = 0
            for payment_term in self.payment_schedule :
                if payment_term.apply_tax == 1 :
                    tax_destribution[payment_term.payment_term] = payment_term.invoice_portion*self.total_taxes_and_charges/100.0000
                    invoice_portions_total += payment_term.invoice_portion
                    print ("invoice_portions_total")
                    print (invoice_portions_total)
                    print ("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
                    print (tax_destribution[payment_term.payment_term])
                    print ("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
                    if payment_term.is_advance == 1:
                        tax_destribution[payment_term.payment_term] = 0
                        advance_invoice_portion = payment_term.invoice_portion

                    if payment_term.is_retention == 1:
                        retention_invoice_portion = payment_term.invoice_portion


            for payment_term in self.payment_schedule :
                if payment_term.apply_tax == 1 and payment_term.is_advance == 0 and payment_term.is_retention == 0:
                    print ("HIT NOT@@")
                    print (invoice_portions_total)
                    tax_destribution[payment_term.payment_term] += (100.0000-invoice_portions_total)*self.total_taxes_and_charges/100.0000
                    break



            detail =frappe.get_list("Payment Terms Template Detail",
                fields=["name","is_advance", "apply_tax","is_retention","payment_term"],
                filters={"parent":self.get("payment_terms_template"),"payment_term":self.payment_term},
                ignore_permissions=True)

            status = "All"

            if detail :
                if detail[0]["is_advance"] ==1:
                    status = "Advance"
                elif detail[0]["is_retention"] ==1:
                    status = "Retention"


            for payment_term in self.payment_schedule :
                debit = payment_term.invoice_portion*self.total /100.0000
                tax = tax_destribution[payment_term.payment_term] if payment_term.payment_term in tax_destribution else 0.00
                if status == "All":
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": payment_term.account,
                            "party_type": "Customer",
                            "party": self.customer,
                            "against": self.against_income_account,
                            "debit":  debit+tax,
                            "title": self.title,
                            "debit_in_account_currency": grand_total_in_company_currency \
                                if self.party_account_currency==self.company_currency else self.grand_total,
                            "against_voucher": self.return_against if cint(self.is_return) else self.name,
                            "against_voucher_type": self.doctype
                        }, self.party_account_currency)
                    )
                else:
                    if payment_term.payment_term == self.payment_term :
                        gl_entries.append(
                            self.get_gl_dict({
                                "account": payment_term.account,
                                "party_type": "Customer",
                                "party": self.customer,
                                "against": self.against_income_account,
                                "debit":  debit+tax,
                                "title": self.title,
                                #~ "debit_in_account_currency": grand_total_in_company_currency \
                                    #~ if self.party_account_currency==self.company_currency else self.grand_total,
                                "debit_in_account_currency": debit+tax,
                                "against_voucher": self.return_against if cint(self.is_return) else self.name,
                                "against_voucher_type": self.doctype
                            }, self.party_account_currency)
                        )

            if advance_invoice_portion != 0:
                print ("#################################################")
                print ("Hit")
                print (invoice_portions_total)
                for tax in self.get("taxes"):
                    if flt(tax.base_tax_amount_after_discount_amount):
                        account_currency = get_account_currency(tax.account_head)
                        print (self.invoice_portion)
                        print (self.total_taxes_and_charges)
                        print (self.invoice_portion*self.total_taxes_and_charges/100.0000)
                        gl_entries.append(
                            self.get_gl_dict({
                                "account": tax.account_head,
                                "against": self.customer,
                                "debit": flt((advance_invoice_portion)*self.total_taxes_and_charges/100.0000),
                                #~ "debit_in_account_currency": flt(tax.base_tax_amount_after_discount_amount) \
                                    #~ if account_currency==self.company_currency else flt(tax.tax_amount_after_discount_amount),
                                "debit_in_account_currency": flt((100.0000-invoice_portions_total)*self.total_taxes_and_charges/100.0000),
                                "cost_center": tax.cost_center
                            }, account_currency)
                        )

                print ("#################################################")


    def make_customer_gl_entry(self, gl_entries):
        if self.grand_total:

            ps_l = self.get_payment_schdual()

            if ps_l:

                grand_total_in_company_currency = flt(self.total * self.conversion_rate,self.precision("total"))
                adv_total = flt(0,self.precision("total"))
                for ps in ps_l :
                    adv_sales_invoice_doc = frappe.get_doc("Sales Invoice",ps.sales_invoice)
                    adv_sales_item_doc = frappe.get_all("Sales Invoice Item", filters={"parent":ps.sales_invoice , "project_payment_schedule":ps.name},
                        fields = ['income_account',"base_amount","amount"], limit=1)

                    adv_income_account = adv_sales_item_doc[0]["income_account"]
                    adv_base_amount = adv_sales_item_doc[0]["base_amount"]
                    adv_amount = adv_sales_item_doc[0]["base_amount"]

                    adv_grand_total_in_company_currency = flt(adv_base_amount)
                    adv_value = flt(adv_grand_total_in_company_currency * flt(ps.billing_percentage) / 100.0000,self.precision("total"))
                    adv_total += adv_value

                    print("ffffffffffffffffffffffffffffFF")
                    print(adv_grand_total_in_company_currency)
                    print(adv_value)
                    print(adv_total)
                    print("gggggggggggggggggggggggggggggggggg")

                    gl_entries.append(
                        self.get_gl_dict({
                        "account": adv_income_account,
                        "party_type": "Customer",
                        "party": self.customer,
                        "against": self.against_income_account,
                        "debit": adv_value,
                        "title": self.title,
                        "debit_in_account_currency": adv_value \
                            if self.party_account_currency==self.company_currency else adv_grand_total_in_company_currency,
                        "against_voucher": self.return_against if cint(self.is_return) else self.name,
                        "against_voucher_type": self.doctype
                        }, self.party_account_currency)
                    )

                gl_entries.append(
                    self.get_gl_dict({
                    "account": self.debit_to,
                    "party_type": "Customer",
                    "party": self.customer,
                    "against": self.against_income_account,
                    "debit": grand_total_in_company_currency-adv_total,
                    "title": self.title,
                    "debit_in_account_currency": grand_total_in_company_currency-adv_total \
                        if self.party_account_currency==self.company_currency else self.grand_total-adv_total,
                    "against_voucher": self.return_against if cint(self.is_return) else self.name,
                    "against_voucher_type": self.doctype
                    }, self.party_account_currency)
                )

            else :
                # Didnot use base_grand_total to book rounding loss gle
                grand_total_in_company_currency = flt(self.grand_total * self.conversion_rate,
                    self.precision("grand_total"))
                gl_entries.append(
                    self.get_gl_dict({
                    "account": self.debit_to,
                    "party_type": "Customer",
                    "party": self.customer,
                    "against": self.against_income_account,
                    "debit": grand_total_in_company_currency,
                    "title": self.title,
                    "debit_in_account_currency": grand_total_in_company_currency \
                        if self.party_account_currency==self.company_currency else self.grand_total,
                    "against_voucher": self.return_against if cint(self.is_return) else self.name,
                    "against_voucher_type": self.doctype
                    }, self.party_account_currency)
                )

    def make_tax_gl_entries(self, gl_entries):
        ps_l = self.get_payment_schdual()
        if ps_l:
            adv_total_tax = flt(0,4)
            total_tax = flt(0,2)
            for ps in ps_l :
                adv_sales_invoice_doc = frappe.get_doc("Sales Invoice",ps.sales_invoice)
                adv_sales_item_doc = frappe.get_all("Sales Invoice Item", filters={"parent":ps.sales_invoice , "project_payment_schedule":ps.name},
                        fields = ['income_account',"base_amount","amount"], limit=1)


                for tax in adv_sales_invoice_doc.get("taxes"):
                    if flt(tax.base_tax_amount_after_discount_amount):
                        account_currency = get_account_currency(tax.account_head)
                        #~ adv_vat = flt(flt(tax.base_tax_amount_after_discount_amount)* flt(ps.billing_percentage) / 100.0000,self.precision("total"))
                        adv_vat = flt(flt(adv_sales_item_doc[0]["base_amount"],4) * flt(ps.billing_percentage,4) / 100.0000,4)
                        print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
                        print(adv_vat)

                        adv_vat = flt(adv_vat * flt(tax.rate) / 100.0000,4)
                        print(adv_vat)
                        adv_total_tax += adv_vat

			for tax in self.get("taxes"):
				if flt(tax.base_tax_amount_after_discount_amount):
					account_currency = get_account_currency(tax.account_head)
					adv_por = flt(adv_total_tax,4) / flt(len(self.taxes),4)
					cr = flt(tax.base_tax_amount_after_discount_amount,4) - adv_por
					total_tax += flt(tax.base_tax_amount_after_discount_amount,4)



			if total_tax-adv_total_tax <.05000:
				pass
			else:
				for tax in adv_sales_invoice_doc.get("taxes"):
					if flt(tax.base_tax_amount_after_discount_amount):
						account_currency = get_account_currency(tax.account_head)
						#~ adv_vat = flt(flt(tax.base_tax_amount_after_discount_amount)* flt(ps.billing_percentage) / 100.0000,self.precision("total"))
						adv_vat = flt(flt(adv_sales_item_doc[0]["base_amount"],4) * flt(ps.billing_percentage,4) / 100.000,4)
						adv_vat = flt(adv_vat * flt(tax.rate) / 100.0000,4)
						gl_entries.append(
							self.get_gl_dict({
								"account": tax.account_head,
								"against": self.customer,
								"credit": adv_vat,
								"credit_in_account_currency": adv_vat \
									if account_currency==self.company_currency else adv_vat,
								"cost_center": tax.cost_center
							}, account_currency)
						)
				for tax in self.get("taxes"):
					if flt(tax.base_tax_amount_after_discount_amount):
						account_currency = get_account_currency(tax.account_head)
						adv_por = flt(adv_total_tax,4) / flt(len(self.taxes),4)
						cr = flt(tax.base_tax_amount_after_discount_amount,4) - adv_por
						gl_entries.append(
							self.get_gl_dict({
								"account": tax.account_head,
								"against": self.customer,
								"credit": cr,
								"credit_in_account_currency": cr,
								"cost_center": tax.cost_center
							}, account_currency)
							)
				gl_entries.append(
                    self.get_gl_dict({
                    "account": self.debit_to,
                    "party_type": "Customer",
                    "party": self.customer,
                    "against": self.against_income_account,
                    "debit": total_tax -adv_total_tax ,
                    "title": self.title,
                    "debit_in_account_currency": total_tax -adv_total_tax \
                        if self.party_account_currency==self.company_currency else total_tax -adv_total_tax,
                    "against_voucher": self.return_against if cint(self.is_return) else self.name,
                    "against_voucher_type": self.doctype
                    }, self.party_account_currency)
                )


        else :
            for tax in self.get("taxes"):
                if flt(tax.base_tax_amount_after_discount_amount):
                    account_currency = get_account_currency(tax.account_head)
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": tax.account_head,
                            "against": self.customer,
                            "credit": flt(tax.base_tax_amount_after_discount_amount),
                            "credit_in_account_currency": flt(tax.base_tax_amount_after_discount_amount) \
                                if account_currency==self.company_currency else flt(tax.tax_amount_after_discount_amount),
                            "cost_center": tax.cost_center
                        }, account_currency)
                    )

    def make_item_gl_entries(self, gl_entries):
        # income account gl entries
        for item in self.get("items"):
            if flt(item.base_net_amount):
                if frappe.db.get_value('Item', item.item_code, 'is_advance_item')  ==1:
                    account_currency = get_account_currency(item.income_account)
                    gl_entries.append(self.get_gl_dict({
                            "account": item.income_account,
                            "against": self.customer,
                            "party_type": "Customer",
                            "party": self.customer,
                            "credit": item.base_net_amount ,
                            "credit_in_account_currency": item.base_net_amount \
                                if account_currency==self.company_currency else item.net_amount,
                            "cost_center": item.cost_center if not self.project else None,
                            "project":self.project,
                            "against_voucher": self.return_against if cint(self.is_return) else self.name,
                            "against_voucher_type": self.doctype
                        }, account_currency)
                    )

                elif item.is_fixed_asset:
                    asset = frappe.get_doc("Asset", item.asset)

                    fixed_asset_gl_entries = get_gl_entries_on_asset_disposal(asset, item.base_net_amount)
                    for gle in fixed_asset_gl_entries:
                        gle["against"] = self.customer
                        gl_entries.append(self.get_gl_dict(gle))

                    asset.db_set("disposal_date", self.posting_date)
                    asset.set_status("Sold" if self.docstatus==1 else None)
                else:
                    account_currency = get_account_currency(item.income_account)
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": item.income_account,
                            "against": self.customer,
                            "credit": item.base_net_amount ,
                            "credit_in_account_currency": item.base_net_amount \
                                if account_currency==self.company_currency else item.net_amount,
                            "cost_center": item.cost_center if not self.project else None,
                            "project":self.project
                        }, account_currency)
                    )

        # expense account gl entries
        if cint(frappe.defaults.get_global_default("auto_accounting_for_stock")) \
                and cint(self.update_stock):
            gl_entries += super(SalesInvoice, self).get_gl_entries()

    def make_pos_gl_entries(self, gl_entries):
        if cint(self.is_pos):
            for payment_mode in self.payments:
                if payment_mode.amount:
                    # POS, make payment entries
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": self.debit_to,
                            "party_type": "Customer",
                            "party": self.customer,
                            "against": payment_mode.account,
                            "credit": payment_mode.base_amount,
                            "credit_in_account_currency": payment_mode.base_amount \
                                if self.party_account_currency==self.company_currency \
                                else payment_mode.amount,
                            "against_voucher": self.return_against if cint(self.is_return) else self.name,
                            "against_voucher_type": self.doctype,
                        }, self.party_account_currency)
                    )

                    payment_mode_account_currency = get_account_currency(payment_mode.account)
                    gl_entries.append(
                        self.get_gl_dict({
                            "account": payment_mode.account,
                            "against": self.customer,
                            "debit": payment_mode.base_amount,
                            "debit_in_account_currency": payment_mode.base_amount \
                                if payment_mode_account_currency==self.company_currency \
                                else payment_mode.amount
                        }, payment_mode_account_currency)
                    )

    def make_gle_for_change_amount(self, gl_entries):
        if cint(self.is_pos) and self.change_amount:
            if self.account_for_change_amount:
                gl_entries.append(
                    self.get_gl_dict({
                        "account": self.debit_to,
                        "party_type": "Customer",
                        "party": self.customer,
                        "against": self.account_for_change_amount,
                        "debit": flt(self.base_change_amount),
                        "debit_in_account_currency": flt(self.base_change_amount) \
                            if self.party_account_currency==self.company_currency else flt(self.change_amount),
                        "against_voucher": self.return_against if cint(self.is_return) else self.name,
                        "against_voucher_type": self.doctype
                    }, self.party_account_currency)
                )

                gl_entries.append(
                    self.get_gl_dict({
                        "account": self.account_for_change_amount,
                        "against": self.customer,
                        "credit": self.base_change_amount
                    })
                )
            else:
                frappe.throw(_("Select change amount account"), title="Mandatory Field")

    def make_write_off_gl_entry(self, gl_entries):
        # write off entries, applicable if only pos
        if self.write_off_account and self.write_off_amount:
            write_off_account_currency = get_account_currency(self.write_off_account)
            default_cost_center = frappe.db.get_value('Company', self.company, 'cost_center')

            gl_entries.append(
                self.get_gl_dict({
                    "account": self.debit_to,
                    "party_type": "Customer",
                    "party": self.customer,
                    "against": self.write_off_account,
                    "credit": self.base_write_off_amount,
                    "credit_in_account_currency": self.base_write_off_amount \
                        if self.party_account_currency==self.company_currency else self.write_off_amount,
                    "against_voucher": self.return_against if cint(self.is_return) else self.name,
                    "against_voucher_type": self.doctype
                }, self.party_account_currency)
            )
            gl_entries.append(
                self.get_gl_dict({
                    "account": self.write_off_account,
                    "against": self.customer,
                    "debit": self.base_write_off_amount,
                    "debit_in_account_currency": self.base_write_off_amount \
                        if write_off_account_currency==self.company_currency else self.write_off_amount,
                    #~ "cost_center": self.write_off_cost_center or default_cost_center
                }, write_off_account_currency)
            )

    def update_billing_status_in_dn(self, update_modified=True):
        updated_delivery_notes = []
        for d in self.get("items"):
            if d.dn_detail:
                billed_amt = frappe.db.sql("""select sum(amount) from `tabSales Invoice Item`
                    where dn_detail=%s and docstatus=1""", d.dn_detail)
                billed_amt = billed_amt and billed_amt[0][0] or 0
                frappe.db.set_value("Delivery Note Item", d.dn_detail, "billed_amt", billed_amt, update_modified=update_modified)
                updated_delivery_notes.append(d.delivery_note)
            elif d.so_detail:
                updated_delivery_notes += update_billed_amount_based_on_so(d.so_detail, update_modified)

        for dn in set(updated_delivery_notes):
            frappe.get_doc("Delivery Note", dn).update_billing_percentage(update_modified=update_modified)

    def on_recurring(self, reference_doc):
        for fieldname in ("c_form_applicable", "c_form_no", "write_off_amount"):
            self.set(fieldname, reference_doc.get(fieldname))

        self.due_date = None



def get_list_context(context=None):
    from erpnext.controllers.website_list_for_contact import get_list_context
    list_context = get_list_context(context)
    list_context.update({
        'show_sidebar': True,
        'show_search': True,
        'no_breadcrumbs': True,
        'title': _('Invoices'),
    })
    return list_context

@frappe.whitelist()
def get_bank_cash_account(mode_of_payment, company):
    account = frappe.db.get_value("Mode of Payment Account",
        {"parent": mode_of_payment, "company": company}, "default_account")
    if not account:
        frappe.throw(_("Please set default Cash or Bank account in Mode of Payment {0}")
            .format(mode_of_payment))
    return {
        "account": account
    }

@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
    def set_missing_values(source, target):
        target.ignore_pricing_rule = 1
        target.run_method("set_missing_values")
        target.run_method("calculate_taxes_and_totals")

    def update_item(source_doc, target_doc, source_parent):
        target_doc.base_amount = (flt(source_doc.qty) - flt(source_doc.delivered_qty)) * \
            flt(source_doc.base_rate)
        target_doc.amount = (flt(source_doc.qty) - flt(source_doc.delivered_qty)) * \
            flt(source_doc.rate)
        target_doc.qty = flt(source_doc.qty) - flt(source_doc.delivered_qty)

    doclist = get_mapped_doc("Sales Invoice", source_name,  {
        "Sales Invoice": {
            "doctype": "Delivery Note",
            "validation": {
                "docstatus": ["=", 1]
            }
        },
        "Sales Invoice Item": {
            "doctype": "Delivery Note Item",
            "field_map": {
                "name": "si_detail",
                "parent": "against_sales_invoice",
                "serial_no": "serial_no",
                "sales_order": "against_sales_order",
                "so_detail": "so_detail"
            },
            "postprocess": update_item,
            "condition": lambda doc: doc.delivered_by_supplier!=1
        },
        "Sales Taxes and Charges": {
            "doctype": "Sales Taxes and Charges",
            "add_if_empty": True
        },
        "Sales Team": {
            "doctype": "Sales Team",
            "field_map": {
                "incentives": "incentives"
            },
            "add_if_empty": True
        }
    }, target_doc, set_missing_values)

    return doclist


@frappe.whitelist()
def make_sales_return(source_name, target_doc=None):
    from erpnext.controllers.sales_and_purchase_return import make_return_doc
    return make_return_doc("Sales Invoice", source_name, target_doc)

def set_account_for_mode_of_payment(self):
    for data in self.payments:
        if not data.account:
            data.account = get_bank_cash_account(data.mode_of_payment, self.company).get("account")
