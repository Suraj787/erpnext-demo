# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import unittest, frappe
from frappe.utils import flt, nowdate
from erpnext.accounts.doctype.account.test_account import get_inventory_account
from erpnext.exceptions import InvalidAccountCurrency

class TestJournalEntry(unittest.TestCase):
	def test_journal_entry_with_against_jv(self):
		jv_invoice = frappe.copy_doc(test_records[2])
		base_jv = frappe.copy_doc(test_records[0])
		self.jv_against_voucher_testcase(base_jv, jv_invoice)

	def test_jv_against_sales_order(self):
		from erpnext.selling.doctype.sales_order.test_sales_order import make_sales_order

		sales_order = make_sales_order(do_not_save=True)
		base_jv = frappe.copy_doc(test_records[0])
		self.jv_against_voucher_testcase(base_jv, sales_order)

	def test_jv_against_purchase_order(self):
		from erpnext.buying.doctype.purchase_order.test_purchase_order import create_purchase_order

		purchase_order = create_purchase_order(do_not_save=True)
		base_jv = frappe.copy_doc(test_records[1])
		self.jv_against_voucher_testcase(base_jv, purchase_order)

	def jv_against_voucher_testcase(self, base_jv, test_voucher):
		dr_or_cr = "credit" if test_voucher.doctype in ["Sales Order", "Journal Entry"] else "debit"

		test_voucher.insert()
		test_voucher.submit()

		if test_voucher.doctype == "Journal Entry":
			self.assertTrue(frappe.db.sql("""select name from `tabJournal Entry Account`
				where account = %s and docstatus = 1 and parent = %s""",
				("_Test Receivable - _TC", test_voucher.name)))

		self.assertFalse(frappe.db.sql("""select name from `tabJournal Entry Account`
			where reference_type = %s and reference_name = %s""", (test_voucher.doctype, test_voucher.name)))

		base_jv.get("accounts")[0].is_advance = "Yes" if (test_voucher.doctype in ["Sales Order", "Purchase Order"]) else "No"
		base_jv.get("accounts")[0].set("reference_type", test_voucher.doctype)
		base_jv.get("accounts")[0].set("reference_name", test_voucher.name)
		base_jv.insert()
		base_jv.submit()

		submitted_voucher = frappe.get_doc(test_voucher.doctype, test_voucher.name)

		self.assertTrue(frappe.db.sql("""select name from `tabJournal Entry Account`
			where reference_type = %s and reference_name = %s and {0}=400""".format(dr_or_cr),
				(submitted_voucher.doctype, submitted_voucher.name)))

		if base_jv.get("accounts")[0].is_advance == "Yes":
			self.advance_paid_testcase(base_jv, submitted_voucher, dr_or_cr)
		self.cancel_against_voucher_testcase(submitted_voucher)

	def advance_paid_testcase(self, base_jv, test_voucher, dr_or_cr):
		#Test advance paid field
		advance_paid = frappe.db.sql("""select advance_paid from `tab%s`
					where name=%s""" % (test_voucher.doctype, '%s'), (test_voucher.name))
		payment_against_order = base_jv.get("accounts")[0].get(dr_or_cr)

		self.assertTrue(flt(advance_paid[0][0]) == flt(payment_against_order))

	def cancel_against_voucher_testcase(self, test_voucher):
		if test_voucher.doctype == "Journal Entry":
			# if test_voucher is a Journal Entry, test cancellation of test_voucher
			test_voucher.cancel()
			self.assertFalse(frappe.db.sql("""select name from `tabJournal Entry Account`
				where reference_type='Journal Entry' and reference_name=%s""", test_voucher.name))

		elif test_voucher.doctype in ["Sales Order", "Purchase Order"]:
			# if test_voucher is a Sales Order/Purchase Order, test error on cancellation of test_voucher
			submitted_voucher = frappe.get_doc(test_voucher.doctype, test_voucher.name)
			self.assertRaises(frappe.LinkExistsError, submitted_voucher.cancel)

	def test_jv_against_stock_account(self):
		from erpnext.stock.doctype.purchase_receipt.test_purchase_receipt import set_perpetual_inventory
		set_perpetual_inventory()

		jv = frappe.copy_doc(test_records[0])
		jv.get("accounts")[0].update({
			"account": get_inventory_account('_Test Company'),
			"company": "_Test Company",
			"party_type": None,
			"party": None
		})

		jv.insert()

		from erpnext.accounts.general_ledger import StockAccountInvalidTransaction
		self.assertRaises(StockAccountInvalidTransaction, jv.submit)

		set_perpetual_inventory(0)

	def test_multi_currency(self):
		jv = make_journal_entry("_Test Bank USD - _TC",
			"_Test Bank - _TC", 100, exchange_rate=50, save=False)

		jv.get("accounts")[1].credit_in_account_currency = 5000
		jv.submit()

		gl_entries = frappe.db.sql("""select account, account_currency, debit, credit,
			debit_in_account_currency, credit_in_account_currency
			from `tabGL Entry` where voucher_type='Journal Entry' and voucher_no=%s
			order by account asc""", jv.name, as_dict=1)

		self.assertTrue(gl_entries)

		expected_values = {
			"_Test Bank USD - _TC": {
				"account_currency": "USD",
				"debit": 5000,
				"debit_in_account_currency": 100,
				"credit": 0,
				"credit_in_account_currency": 0
			},
			"_Test Bank - _TC": {
				"account_currency": "INR",
				"debit": 0,
				"debit_in_account_currency": 0,
				"credit": 5000,
				"credit_in_account_currency": 5000
			}
		}

		for field in ("account_currency", "debit", "debit_in_account_currency", "credit", "credit_in_account_currency"):
			for i, gle in enumerate(gl_entries):
				self.assertEqual(expected_values[gle.account][field], gle[field])

		# cancel
		jv.cancel()

		gle = frappe.db.sql("""select name from `tabGL Entry`
			where voucher_type='Sales Invoice' and voucher_no=%s""", jv.name)

		self.assertFalse(gle)

	def test_disallow_change_in_account_currency_for_a_party(self):
		# create jv in USD
		jv = make_journal_entry("_Test Bank USD - _TC",
			"_Test Receivable USD - _TC", 100, save=False)

		jv.accounts[1].update({
			"party_type": "Customer",
			"party": "_Test Customer USD"
		})

		jv.submit()

		# create jv in USD, but account currency in INR
		jv = make_journal_entry("_Test Bank - _TC",
			"_Test Receivable - _TC", 100, save=False)

		jv.accounts[1].update({
			"party_type": "Customer",
			"party": "_Test Customer USD"
		})

		self.assertRaises(InvalidAccountCurrency, jv.submit)

		# back in USD
		jv = make_journal_entry("_Test Bank USD - _TC",
			"_Test Receivable USD - _TC", 100, save=False)

		jv.accounts[1].update({
			"party_type": "Customer",
			"party": "_Test Customer USD"
		})

		jv.submit()

	def test_inter_company_jv(self):
		frappe.db.set_value("Account", "Sales Expenses - _TC", "inter_company_account", 1)
		frappe.db.set_value("Account", "Buildings - _TC", "inter_company_account", 1)
		frappe.db.set_value("Account", "Sales Expenses - _TC1", "inter_company_account", 1)
		frappe.db.set_value("Account", "Buildings - _TC1", "inter_company_account", 1)
		jv = make_journal_entry("Sales Expenses - _TC", "Buildings - _TC", 100, posting_date=nowdate(), cost_center = "Main - _TC", save=False)
		jv.voucher_type = "Inter Company Journal Entry"
		jv.multi_currency = 0
		jv.insert()
		jv.submit()

		jv1 = make_journal_entry("Sales Expenses - _TC1", "Buildings - _TC1", 100, posting_date=nowdate(), cost_center = "Main - _TC1", save=False)
		jv1.inter_company_journal_entry_reference = jv.name
		jv1.company = "_Test Company 1"
		jv1.voucher_type = "Inter Company Journal Entry"
		jv1.multi_currency = 0
		jv1.insert()
		jv1.submit()

		jv.reload()

		self.assertEqual(jv.inter_company_journal_entry_reference, jv1.name)
		self.assertEqual(jv1.inter_company_journal_entry_reference, jv.name)

		jv.cancel()
		jv1.reload()
		jv.reload()

		self.assertEqual(jv.inter_company_journal_entry_reference, "")
		self.assertEqual(jv1.inter_company_journal_entry_reference, "")

	def test_jv_for_enable_allow_cost_center_in_entry_of_bs_account(self):
		from erpnext.accounts.doctype.cost_center.test_cost_center import create_cost_center
		accounts_settings = frappe.get_doc('Accounts Settings', 'Accounts Settings')
		accounts_settings.allow_cost_center_in_entry_of_bs_account = 1
		accounts_settings.save()
		cost_center = "_Test Cost Center for BS Account - _TC"
		create_cost_center(cost_center_name="_Test Cost Center for BS Account", company="_Test Company")
		jv = make_journal_entry("_Test Cash - _TC", "_Test Bank - _TC", 100, cost_center = cost_center, save=False)
		jv.voucher_type = "Bank Entry"
		jv.multi_currency = 0
		jv.cheque_no = "112233"
		jv.cheque_date = nowdate()
		jv.insert()
		jv.submit()

		expected_values = {
			"_Test Cash - _TC": {
				"cost_center": cost_center
			},
			"_Test Bank - _TC": {
				"cost_center": cost_center
			}
		}

		gl_entries = frappe.db.sql("""select account, cost_center, debit, credit
			from `tabGL Entry` where voucher_type='Journal Entry' and voucher_no=%s
			order by account asc""", jv.name, as_dict=1)

		self.assertTrue(gl_entries)

		for gle in gl_entries:
			self.assertEqual(expected_values[gle.account]["cost_center"], gle.cost_center)

		accounts_settings.allow_cost_center_in_entry_of_bs_account = 0
		accounts_settings.save()

	def test_jv_account_and_party_balance_for_enable_allow_cost_center_in_entry_of_bs_account(self):
		from erpnext.accounts.doctype.cost_center.test_cost_center import create_cost_center
		from erpnext.accounts.utils import get_balance_on
		accounts_settings = frappe.get_doc('Accounts Settings', 'Accounts Settings')
		accounts_settings.allow_cost_center_in_entry_of_bs_account = 1
		accounts_settings.save()
		cost_center = "_Test Cost Center for BS Account - _TC"
		create_cost_center(cost_center_name="_Test Cost Center for BS Account", company="_Test Company")
		jv = make_journal_entry("_Test Cash - _TC", "_Test Bank - _TC", 100, cost_center = cost_center, save=False)
		account_balance = get_balance_on(account="_Test Bank - _TC", cost_center=cost_center)
		jv.voucher_type = "Bank Entry"
		jv.multi_currency = 0
		jv.cheque_no = "112233"
		jv.cheque_date = nowdate()
		jv.insert()
		jv.submit()

		expected_account_balance = account_balance - 100
		account_balance = get_balance_on(account="_Test Bank - _TC", cost_center=cost_center)
		self.assertEqual(expected_account_balance, account_balance)

		accounts_settings.allow_cost_center_in_entry_of_bs_account = 0
		accounts_settings.save()

def make_journal_entry(account1, account2, amount, cost_center=None, posting_date=None, exchange_rate=1, save=True, submit=False, project=None):
	if not cost_center:
		cost_center = "_Test Cost Center - _TC"

	jv = frappe.new_doc("Journal Entry")
	jv.posting_date = posting_date or nowdate()
	jv.company = "_Test Company"
	jv.user_remark = "test"
	jv.multi_currency = 1
	jv.set("accounts", [
		{
			"account": account1,
			"cost_center": cost_center,
			"project": project,
			"debit_in_account_currency": amount if amount > 0 else 0,
			"credit_in_account_currency": abs(amount) if amount < 0 else 0,
			"exchange_rate": exchange_rate
		}, {
			"account": account2,
			"cost_center": cost_center,
			"project": project,
			"credit_in_account_currency": amount if amount > 0 else 0,
			"debit_in_account_currency": abs(amount) if amount < 0 else 0,
			"exchange_rate": exchange_rate
		}
	])
	if save or submit:
		jv.insert()

		if submit:
			jv.submit()

	return jv

test_records = frappe.get_test_records('Journal Entry')
