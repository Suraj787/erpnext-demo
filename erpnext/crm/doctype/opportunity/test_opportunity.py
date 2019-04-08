# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.utils import today
from erpnext.crm.doctype.lead.lead import make_customer
from erpnext.crm.doctype.opportunity.opportunity import make_quotation
import unittest

test_records = frappe.get_test_records('Opportunity')

class TestOpportunity(unittest.TestCase):
	def test_opportunity_status(self):
		doc = make_opportunity(with_items=0)
		quotation = make_quotation(doc.name)
		quotation.append('items', {
			"item_code": "_Test Item",
			"qty": 1
		})

		quotation.run_method("set_missing_values")
		quotation.run_method("calculate_taxes_and_totals")
		quotation.submit()

		doc = frappe.get_doc('Opportunity', doc.name)
		self.assertEqual(doc.status, "Quotation")

	def test_make_new_lead_if_required(self):
		args = {
			"doctype": "Opportunity",
			"contact_email":"new.opportunity@example.com",
			"opportunity_type": "Sales",
			"with_items": 0,
			"transaction_date": today()
		}
		# new lead should be created against the new.opportunity@example.com
		opp_doc = frappe.get_doc(args).insert(ignore_permissions=True)

		self.assertTrue(opp_doc.lead)
		self.assertEqual(opp_doc.enquiry_from, "Lead")
		self.assertEqual(frappe.db.get_value("Lead", opp_doc.lead, "email_id"),
			'new.opportunity@example.com')

		# create new customer and create new contact against 'new.opportunity@example.com'
		customer = make_customer(opp_doc.lead).insert(ignore_permissions=True)
		frappe.get_doc({
			"doctype": "Contact",
			"email_id": "new.opportunity@example.com",
			"first_name": "_Test Opportunity Customer",
			"links": [{
				"link_doctype": "Customer",
				"link_name": customer.name
			}]
		}).insert(ignore_permissions=True)

		opp_doc = frappe.get_doc(args).insert(ignore_permissions=True)
		self.assertTrue(opp_doc.customer)
		self.assertEqual(opp_doc.enquiry_from, "Customer")
		self.assertEqual(opp_doc.customer, customer.name)

def make_opportunity(**args):
	args = frappe._dict(args)

	opp_doc = frappe.get_doc({
		"doctype": "Opportunity",
		"company": args.company or "_Test Company",
		"enquiry_from": args.enquiry_from or "Customer",
		"opportunity_type": "Sales",
		"with_items": args.with_items or 0,
		"transaction_date": today()
	})

	if opp_doc.enquiry_from == 'Customer':
		opp_doc.customer = args.customer or "_Test Customer"

	if opp_doc.enquiry_from == 'Lead':
		opp_doc.customer = args.lead or "_T-Lead-00001"

	if args.with_items:
		opp_doc.append('items', {
			"item_code": args.item_code or "_Test Item",
			"qty": args.qty or 1
		})

	opp_doc.insert()
	return opp_doc