# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint
from erpnext.stock import get_warehouse_account_map
from erpnext.controllers.stock_controller import update_gl_entries_after

def execute():
	company_list = frappe.db.sql_list("""Select name from tabCompany where enable_perpetual_inventory = 1""")
	frappe.reload_doc('accounts', 'doctype', 'sales_invoice')
	
	frappe.reload_doctype("Purchase Invoice")	
	wh_account = get_warehouse_account_map()
	
	for pi in frappe.get_all("Purchase Invoice", fields=["name", "company"], filters={"docstatus": 1, "update_stock": 1}):
		if pi.company in company_list:
			pi_doc = frappe.get_doc("Purchase Invoice", pi.name)
			items, warehouses = pi_doc.get_items_and_warehouses()
			update_gl_entries_after(pi_doc.posting_date, pi_doc.posting_time, warehouses, items, wh_account)
		
			frappe.db.commit()