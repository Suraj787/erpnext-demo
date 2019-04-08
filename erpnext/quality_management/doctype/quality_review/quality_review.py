# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import datetime
class QualityReview(Document):
	pass

def review():
	now = datetime.datetime.now()
	day = now.day
	day_name = now.strftime("%A")
	month=now.strftime("%B")

	for data in frappe.get_all("Quality Goal",fields=['name', 'frequency', 'date', 'weekly', 'measurable']):
		if data.frequency == 'Daily':
			create_review(data.name, data.measurable)

		elif data.frequency == 'Weekly':
			if data.weekly == day_name:
				create_review(data.name, data.measurable)

		elif data.frequency == 'Monthly':
			if data.date == str(day):
				create_review(data.name, data.measurable)

		elif data.frequency == 'Quarterly':
			if (month == 'January' or month == 'April' or month == 'July' or month == 'October') and str(day) == data.date:
				create_review(data.name, data.measurable)

		elif data.frequency == 'Half Yearly':
			if (month == 'January' or month == 'July') and str(day) == data.date:
				create_review(data.name, data.measurable)

		elif data.frequency == 'Yearly':
			if month == data.yearly and str(day) == data.date:
				create_review(data.name, data.measurable)

		else:
			pass

def create_review(name, measurable):
	objectives = frappe.get_all("Quality Objective", filters={'parent': name }, fields=['objective', 'target', 'unit'])
	doc = frappe.get_doc({
		"doctype": "Quality Review",
   		"goal": name,
   		"date": frappe.as_unicode(frappe.utils.nowdate()),
		"measurable": measurable,
	})
	if measurable == 'Yes':
		for objective in objectives:
			doc.append("values",{
				'objective': objective.objective,
				'target': objective.target,
				'achieved': 0,
				'unit': objective.unit
			})
	else:
		for objective in objectives:
			doc.append("values",{
				'objective': objective.objective,
			})
	doc.insert()
	frappe.db.commit()