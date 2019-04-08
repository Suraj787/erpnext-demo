# Copyright (c) 2015, Frappe Technologies Pvt. Ltd.
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe, erpnext
from frappe import _, scrub
from frappe.utils import getdate, nowdate, flt, cint, formatdate, cstr

class ReceivablePayableReport(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.filters.report_date = getdate(self.filters.report_date or nowdate())
		self.age_as_on = getdate(nowdate()) \
			if self.filters.report_date > getdate(nowdate()) \
			else self.filters.report_date

	def run(self, args):
		party_naming_by = frappe.db.get_value(args.get("naming_by")[0], None, args.get("naming_by")[1])
		columns = self.get_columns(party_naming_by, args)
		data = self.get_data(party_naming_by, args)
		chart = self.get_chart_data(columns, data)
		return columns, data, None, chart

	def get_columns(self, party_naming_by, args):
		columns = []
		columns.append({
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"fieldname": "posting_date",
			"width": 90
		})

		columns += [_(args.get("party_type")) + ":Link/" + args.get("party_type") + ":200"]

		if args.get("party_type") == 'Customer':
			columns.append({
				"label": _("Customer Contact"),
				"fieldtype": "Link",
				"fieldname": "contact",
				"options":"Contact",
				"width": 100
			})

		if party_naming_by == "Naming Series":
			columns += [args.get("party_type") + " Name::110"]

		columns.append({
			"label": _("Voucher Type"),
			"fieldtype": "Data",
			"fieldname": "voucher_type",
			"width": 110
		})

		columns.append({
			"label": _("Voucher No"),
			"fieldtype": "Dynamic Link",
			"fieldname": "voucher_no",
			"width": 110,
			"options": "voucher_type",
		})

		columns += [_("Due Date") + ":Date:80"]

		if args.get("party_type") == "Supplier":
			columns += [_("Bill No") + "::80", _("Bill Date") + ":Date:80"]

		credit_or_debit_note = "Credit Note" if args.get("party_type") == "Customer" else "Debit Note"

		if self.filters.based_on_payment_terms:
			columns.append({
				"label": "Payment Term",
				"fieldname": "payment_term",
				"fieldtype": "Data",
				"width": 120
			})
			columns.append({
				"label": "Invoice Grand Total",
				"fieldname": "invoice_grand_total",
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120
			})

		for label in ("Invoiced Amount", "Paid Amount", credit_or_debit_note, "Outstanding Amount"):
			columns.append({
				"label": label,
				"fieldname": frappe.scrub(label),
				"fieldtype": "Currency",
				"options": "currency",
				"width": 120
			})

		columns += [_("Age (Days)") + ":Int:80"]

		self.ageing_col_idx_start = len(columns)

		if not "range1" in self.filters:
			self.filters["range1"] = "30"
		if not "range2" in self.filters:
			self.filters["range2"] = "60"
		if not "range3" in self.filters:
			self.filters["range3"] = "90"

		for label in ("0-{range1}".format(range1=self.filters["range1"]),
			"{range1}-{range2}".format(range1=cint(self.filters["range1"])+ 1, range2=self.filters["range2"]),
			"{range2}-{range3}".format(range2=cint(self.filters["range2"])+ 1, range3=self.filters["range3"]),
			"{range3}-{above}".format(range3=cint(self.filters["range3"])+ 1, above=_("Above"))):
				columns.append({
					"label": label,
					"fieldname":label,
					"fieldtype": "Currency",
					"options": "currency",
					"width": 120
				})

		columns += [
		{
			"fieldname": "currency",
			"label": _("Currency"),
			"fieldtype": "Link",
			"options": "Currency",
			"width": 100
		},
		{
			"fieldname": "pdc/lc_ref",
			"label": _("PDC/LC Ref"),
			"fieldtype": "Data",
			"width": 110
		},
		{
			"fieldname": "pdc/lc_amount",
			"label": _("PDC/LC Amount"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130
		},
		{
			"fieldname": "remaining_balance",
			"label": _("Remaining Balance"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 130
		}]

		if args.get('party_type') == 'Customer':
			columns += [
				{
					"label": _("Customer LPO"),
					"fieldtype": "Data",
					"fieldname": "po_no",
					"width": 100,
				},
				_("Delivery Note") + ":Data:100",
				_("Territory") + ":Link/Territory:80",
				_("Customer Group") + ":Link/Customer Group:120",
				{
					"label": _("Sales Person"),
					"fieldtype": "Data",
					"fieldname": "sales_person",
					"width": 120,
				}
			]
		if args.get("party_type") == "Supplier":
			columns += [_("Supplier Group") + ":Link/Supplier Group:80"]

		columns.append(_("Remarks") + "::200")

		return columns

	def get_data(self, party_naming_by, args):
		from erpnext.accounts.utils import get_currency_precision
		self.currency_precision = get_currency_precision() or 2
		self.dr_or_cr = "debit" if args.get("party_type") == "Customer" else "credit"

		future_vouchers = self.get_entries_after(self.filters.report_date, args.get("party_type"))

		if not self.filters.get("company"):
			self.filters["company"] = frappe.db.get_single_value('Global Defaults', 'default_company')

		self.company_currency = frappe.get_cached_value('Company',  self.filters.get("company"), "default_currency")

		return_entries = self.get_return_entries(args.get("party_type"))

		data = []
		self.pdc_details = get_pdc_details(args.get("party_type"), self.filters.report_date)
		gl_entries_data = self.get_entries_till(self.filters.report_date, args.get("party_type"))

		if gl_entries_data:
			voucher_nos = [d.voucher_no for d in gl_entries_data] or []
			dn_details = get_dn_details(args.get("party_type"), voucher_nos)
			self.voucher_details = get_voucher_details(args.get("party_type"), voucher_nos, dn_details)

		if self.filters.based_on_payment_terms and gl_entries_data:
			self.payment_term_map = self.get_payment_term_detail(voucher_nos)

		for gle in gl_entries_data:
			if self.is_receivable_or_payable(gle, self.dr_or_cr, future_vouchers):
				outstanding_amount, credit_note_amount, payment_amount = self.get_outstanding_amount(
					gle,self.filters.report_date, self.dr_or_cr, return_entries)

				temp_outstanding_amt = outstanding_amount
				temp_credit_note_amt = credit_note_amount

				if abs(outstanding_amount) > 0.1/10**self.currency_precision:
					if self.filters.based_on_payment_terms and self.payment_term_map.get(gle.voucher_no):
						for d in self.payment_term_map.get(gle.voucher_no):
							# Allocate payment amount based on payment terms(FIFO order)
							payment_amount, d.payment_amount = self.allocate_based_on_fifo(payment_amount, d.payment_term_amount)

							term_outstanding_amount = d.payment_term_amount - d.payment_amount

							# Allocate credit note based on payment terms(FIFO order)
							credit_note_amount, d.credit_note_amount = self.allocate_based_on_fifo(credit_note_amount, term_outstanding_amount)

							term_outstanding_amount -= d.credit_note_amount

							row_outstanding = term_outstanding_amount
							# Allocate PDC based on payment terms(FIFO order)
							d.pdc_details, d.pdc_amount = self.allocate_pdc_amount_in_fifo(gle, row_outstanding)

							if term_outstanding_amount > 0:
								row = self.prepare_row(party_naming_by, args, gle, term_outstanding_amount,
									d.credit_note_amount, d.due_date, d.payment_amount , d.payment_term_amount,
									d.description, d.pdc_amount, d.pdc_details)
								data.append(row)

						if credit_note_amount:
							row = self.prepare_row_without_payment_terms(party_naming_by, args, gle, temp_outstanding_amt,
								temp_credit_note_amt)
							data.append(row)

					else:
						row = self.prepare_row_without_payment_terms(party_naming_by, args, gle, outstanding_amount,
							credit_note_amount)
						data.append(row)
		return data

	def allocate_pdc_amount_in_fifo(self, gle, row_outstanding):
		pdc_list = self.pdc_details.get((gle.voucher_no, gle.party), [])

		pdc_details = []
		pdc_amount = 0
		for pdc in pdc_list:
			if row_outstanding <= pdc.pdc_amount:
				pdc_amount += row_outstanding
				pdc.pdc_amount -= row_outstanding
				if row_outstanding and pdc.pdc_ref and pdc.pdc_date:
					pdc_details.append(cstr(pdc.pdc_ref) + "/" + formatdate(pdc.pdc_date))
				row_outstanding = 0

			else:
				pdc_amount = pdc.pdc_amount
				if pdc.pdc_amount and pdc.pdc_ref and pdc.pdc_date:
					pdc_details.append(cstr(pdc.pdc_ref) + "/" + formatdate(pdc.pdc_date))
				pdc.pdc_amount = 0
				row_outstanding -= pdc_amount

		return pdc_details, pdc_amount

	def prepare_row_without_payment_terms(self, party_naming_by, args, gle, outstanding_amount, credit_note_amount):
		pdc_list = self.pdc_details.get((gle.voucher_no, gle.party), [])
		pdc_amount = 0
		pdc_details = []
		for d in pdc_list:
			pdc_amount += flt(d.pdc_amount)
			if pdc_amount and d.pdc_ref and d.pdc_date:
				pdc_details.append(cstr(d.pdc_ref) + "/" + formatdate(d.pdc_date))

		row = self.prepare_row(party_naming_by, args, gle, outstanding_amount,
			credit_note_amount, pdc_amount=pdc_amount, pdc_details=pdc_details)

		return row


	def allocate_based_on_fifo(self, total_amount, row_amount):
		allocated_amount = 0
		if row_amount <= total_amount:
			allocated_amount = row_amount
			total_amount -= row_amount
		else:
			allocated_amount = total_amount
			total_amount = 0

		return total_amount, allocated_amount

	def prepare_row(self, party_naming_by, args, gle, outstanding_amount, credit_note_amount,
		due_date=None, paid_amt=None, payment_term_amount=None, payment_term=None, pdc_amount=None, pdc_details=None):
		row = [gle.posting_date, gle.party]

		# customer / supplier name
		if party_naming_by == "Naming Series":
			row += [self.get_party_name(gle.party_type, gle.party)]

		if args.get("party_type") == 'Customer':
			row += [self.get_customer_contact(gle.party_type, gle.party)]

		# get due date
		if not due_date:
			due_date = self.voucher_details.get(gle.voucher_no, {}).get("due_date", "")
		bill_date = self.voucher_details.get(gle.voucher_no, {}).get("bill_date", "")

		row += [gle.voucher_type, gle.voucher_no, due_date]

		# get supplier bill details
		if args.get("party_type") == "Supplier":
			row += [
				self.voucher_details.get(gle.voucher_no, {}).get("bill_no", ""),
				self.voucher_details.get(gle.voucher_no, {}).get("bill_date", "")
			]

		# invoiced and paid amounts
		invoiced_amount = gle.get(self.dr_or_cr) if (gle.get(self.dr_or_cr) > 0) else 0

		if self.filters.based_on_payment_terms:
			row+=[payment_term, invoiced_amount]
			if payment_term_amount:
				invoiced_amount = payment_term_amount

		if not payment_term_amount:
			paid_amt = invoiced_amount - outstanding_amount - credit_note_amount
		row += [invoiced_amount, paid_amt, credit_note_amount, outstanding_amount]

		# ageing data
		if self.filters.ageing_based_on == "Due Date":
			entry_date = due_date
		elif self.filters.ageing_based_on == "Supplier Invoice Date":
			entry_date = bill_date
		else:
			entry_date = gle.posting_date

		row += get_ageing_data(cint(self.filters.range1), cint(self.filters.range2),
			cint(self.filters.range3), self.age_as_on, entry_date, outstanding_amount)


		# issue 6371-Ageing buckets should not have amounts if due date is not reached
		if self.filters.ageing_based_on == "Due Date" \
				and getdate(due_date) > getdate(self.filters.report_date):
			row[-1]=row[-2]=row[-3]=row[-4]=0

		if self.filters.ageing_based_on == "Supplier Invoice Date" \
				and getdate(bill_date) > getdate(self.filters.report_date):

			row[-1]=row[-2]=row[-3]=row[-4]=0

		if self.filters.get(scrub(args.get("party_type"))):
			row.append(gle.account_currency)
		else:
			row.append(self.company_currency)

		remaining_balance = outstanding_amount - flt(pdc_amount)
		pdc_details = ", ".join(pdc_details)
		row += [pdc_details, pdc_amount, remaining_balance]

		if args.get('party_type') == 'Customer':
			# customer LPO
			row += [self.voucher_details.get(gle.voucher_no, {}).get("po_no")]

			# Delivery Note
			row += [self.voucher_details.get(gle.voucher_no, {}).get("delivery_note")]

		# customer territory / supplier group
		if args.get("party_type") == "Customer":
			row += [self.get_territory(gle.party), self.get_customer_group(gle.party),
				self.voucher_details.get(gle.voucher_no, {}).get("sales_person")]
		if args.get("party_type") == "Supplier":
			row += [self.get_supplier_group(gle.party)]

		row.append(gle.remarks)

		return row

	def get_entries_after(self, report_date, party_type):
		# returns a distinct list
		return list(set([(e.voucher_type, e.voucher_no) for e in self.get_gl_entries(party_type, report_date, for_future=True)]))

	def get_entries_till(self, report_date, party_type):
		# returns a generator
		return self.get_gl_entries(party_type, report_date)

	def is_receivable_or_payable(self, gle, dr_or_cr, future_vouchers):
		return (
			# advance
			(not gle.against_voucher) or

			# against sales order/purchase order
			(gle.against_voucher_type in ["Sales Order", "Purchase Order"]) or

			# sales invoice/purchase invoice
			(gle.against_voucher==gle.voucher_no and gle.get(dr_or_cr) > 0) or

			# entries adjusted with future vouchers
			((gle.against_voucher_type, gle.against_voucher) in future_vouchers)
		)

	def get_return_entries(self, party_type):
		doctype = "Sales Invoice" if party_type=="Customer" else "Purchase Invoice"
		return [d.name for d in frappe.get_all(doctype, filters={"is_return": 1, "docstatus": 1})]

	def get_outstanding_amount(self, gle, report_date, dr_or_cr, return_entries):
		payment_amount, credit_note_amount = 0.0, 0.0
		reverse_dr_or_cr = "credit" if dr_or_cr=="debit" else "debit"

		for e in self.get_gl_entries_for(gle.party, gle.party_type, gle.voucher_type, gle.voucher_no):
			if getdate(e.posting_date) <= report_date and e.name!=gle.name:
				amount = flt(e.get(reverse_dr_or_cr), self.currency_precision) - flt(e.get(dr_or_cr), self.currency_precision)
				if e.voucher_no not in return_entries:
					payment_amount += amount
				else:
					credit_note_amount += amount

		outstanding_amount = (flt((flt(gle.get(dr_or_cr), self.currency_precision)
			- flt(gle.get(reverse_dr_or_cr), self.currency_precision)
			- payment_amount - credit_note_amount), self.currency_precision))

		credit_note_amount = flt(credit_note_amount, self.currency_precision)

		return outstanding_amount, credit_note_amount, payment_amount

	def get_party_name(self, party_type, party_name):
		return self.get_party_map(party_type).get(party_name, {}).get("customer_name" if party_type == "Customer" else "supplier_name") or ""

	def get_customer_contact(self, party_type, party_name):
		return self.get_party_map(party_type).get(party_name, {}).get("customer_primary_contact")

	def get_territory(self, party_name):
		return self.get_party_map("Customer").get(party_name, {}).get("territory") or ""

	def get_customer_group(self, party_name):
		return self.get_party_map("Customer").get(party_name, {}).get("customer_group") or ""

	def get_supplier_group(self, party_name):
		return self.get_party_map("Supplier").get(party_name, {}).get("supplier_group") or ""

	def get_party_map(self, party_type):
		if not hasattr(self, "party_map"):
			if party_type == "Customer":
				select_fields = "name, customer_name, territory, customer_group, customer_primary_contact"
			elif party_type == "Supplier":
				select_fields = "name, supplier_name, supplier_group"

			self.party_map = dict(((r.name, r) for r in frappe.db.sql("select {0} from `tab{1}`"
				.format(select_fields, party_type), as_dict=True)))

		return self.party_map

	def get_gl_entries(self, party_type, date=None, for_future=False):
		conditions, values = self.prepare_conditions(party_type)

		if self.filters.get(scrub(party_type)):
			select_fields = "sum(debit_in_account_currency) as debit, sum(credit_in_account_currency) as credit"
		else:
			select_fields = "sum(debit) as debit, sum(credit) as credit"

		if date and not for_future:
			conditions += " and posting_date <= '%s'" % date

		if date and for_future:
			conditions += " and posting_date > '%s'" % date

		self.gl_entries = frappe.db.sql("""
			select
				name, posting_date, account, party_type, party, voucher_type, voucher_no,
				against_voucher_type, against_voucher, account_currency, remarks, {0}
			from
				`tabGL Entry`
			where
				docstatus < 2 and party_type=%s and (party is not null and party != '') {1}
				group by voucher_type, voucher_no, against_voucher_type, against_voucher, party
				order by posting_date, party"""
			.format(select_fields, conditions), values, as_dict=True)

		return self.gl_entries

	def prepare_conditions(self, party_type):
		conditions = [""]
		values = [party_type]

		party_type_field = scrub(party_type)

		if self.filters.company:
			conditions.append("company=%s")
			values.append(self.filters.company)

		company_finance_book = erpnext.get_default_finance_book(self.filters.company)

		if not self.filters.finance_book or (self.filters.finance_book == company_finance_book):
			conditions.append("ifnull(finance_book,'') in (%s, '')")
			values.append(company_finance_book)
		elif self.filters.finance_book:
			conditions.append("ifnull(finance_book,'') = %s")
			values.append(self.filters.finance_book)

		if self.filters.get(party_type_field):
			conditions.append("party=%s")
			values.append(self.filters.get(party_type_field))

		if party_type_field=="customer":
			account_type = "Receivable"
			if self.filters.get("customer_group"):
				lft, rgt = frappe.db.get_value("Customer Group",
					self.filters.get("customer_group"), ["lft", "rgt"])

				conditions.append("""party in (select name from tabCustomer
					where exists(select name from `tabCustomer Group` where lft >= {0} and rgt <= {1}
						and name=tabCustomer.customer_group))""".format(lft, rgt))

			if self.filters.get("territory"):
				lft, rgt = frappe.db.get_value("Territory",
					self.filters.get("territory"), ["lft", "rgt"])

				conditions.append("""party in (select name from tabCustomer
					where exists(select name from `tabTerritory` where lft >= {0} and rgt <= {1}
						and name=tabCustomer.territory))""".format(lft, rgt))

			if self.filters.get("payment_terms_template"):
				conditions.append("party in (select name from tabCustomer where payment_terms=%s)")
				values.append(self.filters.get("payment_terms_template"))

			if self.filters.get("sales_partner"):
				conditions.append("party in (select name from tabCustomer where default_sales_partner=%s)")
				values.append(self.filters.get("sales_partner"))

			if self.filters.get("sales_person"):
				lft, rgt = frappe.db.get_value("Sales Person",
					self.filters.get("sales_person"), ["lft", "rgt"])

				conditions.append("""exists(select name from `tabSales Team` steam where
					steam.sales_person in (select name from `tabSales Person` where lft >= {0} and rgt <= {1})
					and ((steam.parent = voucher_no and steam.parenttype = voucher_type)
						or (steam.parent = against_voucher and steam.parenttype = against_voucher_type)
						or (steam.parent = party and steam.parenttype = 'Customer')))""".format(lft, rgt))

		elif party_type_field=="supplier":
			account_type = "Payable"
			if self.filters.get("supplier_group"):
				conditions.append("""party in (select name from tabSupplier
					where supplier_group=%s)""")
				values.append(self.filters.get("supplier_group"))

		accounts = [d.name for d in frappe.get_all("Account",
			filters={"account_type": account_type, "company": self.filters.company})]
		conditions.append("account in (%s)" % ','.join(['%s'] *len(accounts)))
		values += accounts

		return " and ".join(conditions), values

	def get_gl_entries_for(self, party, party_type, against_voucher_type, against_voucher):
		if not hasattr(self, "gl_entries_map"):
			self.gl_entries_map = {}
			for gle in self.get_gl_entries(party_type):
				if gle.against_voucher_type and gle.against_voucher:
					self.gl_entries_map.setdefault(gle.party, {})\
						.setdefault(gle.against_voucher_type, {})\
						.setdefault(gle.against_voucher, [])\
						.append(gle)

		return self.gl_entries_map.get(party, {})\
			.get(against_voucher_type, {})\
			.get(against_voucher, [])

	def get_payment_term_detail(self, voucher_nos):
		payment_term_map = frappe._dict()
		payment_terms_details = frappe.db.sql(""" select si.name,
			party_account_currency, currency, si.conversion_rate,
			ps.due_date, ps.payment_amount, ps.description
			from `tabSales Invoice` si, `tabPayment Schedule` ps
			where si.name = ps.parent and
			si.docstatus = 1 and si.company = %s and
			si.name in (%s) order by ps.due_date
		"""	% (frappe.db.escape(self.filters.company), ','.join(['%s'] *len(voucher_nos))),
		(tuple(voucher_nos)), as_dict = 1)

		for d in payment_terms_details:
			if self.filters.get("customer") and d.currency == d.party_account_currency:
				payment_term_amount = d.payment_amount
			else:
				payment_term_amount = flt(flt(d.payment_amount) * flt(d.conversion_rate), self.currency_precision)

			payment_term_map.setdefault(d.name, []).append(frappe._dict({
				"due_date": d.due_date,
				"payment_term_amount": payment_term_amount,
				"description": d.description
			}))
		return payment_term_map

	def get_chart_data(self, columns, data):
		ageing_columns = columns[self.ageing_col_idx_start : self.ageing_col_idx_start+4]

		rows = []
		for d in data:
			rows.append(
				{
					'values': d[self.ageing_col_idx_start : self.ageing_col_idx_start+4]
				}
			)

		return {
			"data": {
				'labels': [d.get("label") for d in ageing_columns],
				'datasets': rows
			},
			"type": 'percentage'
		}

def execute(filters=None):
	args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}
	return ReceivablePayableReport(filters).run(args)

def get_ageing_data(first_range, second_range, third_range, age_as_on, entry_date, outstanding_amount):
	# [0-30, 30-60, 60-90, 90-above]
	outstanding_range = [0.0, 0.0, 0.0, 0.0]

	if not (age_as_on and entry_date):
		return [0] + outstanding_range

	age = (getdate(age_as_on) - getdate(entry_date)).days or 0
	index = None
	for i, days in enumerate([first_range, second_range, third_range]):
		if age <= days:
			index = i
			break

	if index is None: index = 3
	outstanding_range[index] = outstanding_amount

	return [age] + outstanding_range

def get_pdc_details(party_type, report_date):
	pdc_details = frappe._dict()
	pdc_via_pe = frappe.db.sql("""
		select
			pref.reference_name as invoice_no, pent.party, pent.party_type,
			pent.posting_date as pdc_date, ifnull(pref.allocated_amount,0) as pdc_amount,
			pent.reference_no as pdc_ref
		from
			`tabPayment Entry` as pent inner join `tabPayment Entry Reference` as pref
		on
			(pref.parent = pent.name)
		where
			pent.docstatus < 2 and pent.posting_date > %s
			and pent.party_type = %s
		""", (report_date, party_type), as_dict=1)

	for pdc in pdc_via_pe:
			pdc_details.setdefault((pdc.invoice_no, pdc.party), []).append(pdc)

	if scrub(party_type):
		amount_field = ("jea.debit_in_account_currency"
			if party_type == 'Supplier' else "jea.credit_in_account_currency")
	else:
		amount_field = "jea.debit + jea.credit"

	pdc_via_je = frappe.db.sql("""
		select
			jea.reference_name as invoice_no, jea.party, jea.party_type,
			je.posting_date as pdc_date, ifnull({0},0) as pdc_amount,
			je.cheque_no as pdc_ref
		from
			`tabJournal Entry` as je inner join `tabJournal Entry Account` as jea
		on
			(jea.parent = je.name)
		where
			je.docstatus < 2 and je.posting_date > %s
			and jea.party_type = %s
		""".format(amount_field), (report_date, party_type), as_dict=1)

	for pdc in pdc_via_je:
		pdc_details.setdefault((pdc.invoice_no, pdc.party), []).append(pdc)

	return pdc_details

def get_dn_details(party_type, voucher_nos):
	dn_details = frappe._dict()

	if party_type == "Customer":
		for si in frappe.db.sql("""
			select
				parent, GROUP_CONCAT(delivery_note SEPARATOR ', ') as dn
			from
				`tabSales Invoice Item`
			where
				docstatus=1 and delivery_note is not null and delivery_note != ''
				and parent in (%s) group by parent
			""" %(','.join(['%s'] * len(voucher_nos))), tuple(voucher_nos) , as_dict=1):
			dn_details.setdefault(si.parent, si.dn)

		for si in frappe.db.sql("""
			select
				against_sales_invoice as parent, GROUP_CONCAT(parent SEPARATOR ', ') as dn
			from
				`tabDelivery Note Item`
			where
				docstatus=1 and against_sales_invoice is not null and against_sales_invoice != ''
				and against_sales_invoice in (%s)
				group by against_sales_invoice
			""" %(','.join(['%s'] * len(voucher_nos))), tuple(voucher_nos) , as_dict=1):
			if si.parent in dn_details:
				dn_details[si.parent] += ', %s' %(si.dn)
			else:
				dn_details.setdefault(si.parent, si.dn)

	return dn_details

def get_voucher_details(party_type, voucher_nos, dn_details):
	voucher_details = frappe._dict()

	if party_type == "Customer":
		for si in frappe.db.sql("""
			select inv.name, inv.due_date, inv.po_no, GROUP_CONCAT(steam.sales_person SEPARATOR ', ') as sales_person
			from `tabSales Invoice` inv
			left join `tabSales Team` steam on steam.parent = inv.name and steam.parenttype = 'Sales Invoice'
			where inv.docstatus=1 and inv.name in (%s)
			group by inv.name
			""" %(','.join(['%s'] *len(voucher_nos))), (tuple(voucher_nos)), as_dict=1):
				si['delivery_note'] = dn_details.get(si.name)
				voucher_details.setdefault(si.name, si)

	if party_type == "Supplier":
		for pi in frappe.db.sql("""select name, due_date, bill_no, bill_date
			from `tabPurchase Invoice` where docstatus = 1 and name in (%s)
			""" %(','.join(['%s'] *len(voucher_nos))), (tuple(voucher_nos)), as_dict=1):
			voucher_details.setdefault(pi.name, pi)

	for pi in frappe.db.sql("""select name, due_date, bill_no, bill_date from
		`tabJournal Entry` where docstatus = 1 and bill_no is not NULL and name in (%s)
		""" %(','.join(['%s'] *len(voucher_nos))), (tuple(voucher_nos)), as_dict=1):
			voucher_details.setdefault(pi.name, pi)

	return voucher_details
