# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from erpnext.quality_management.doctype.quality_procedure.test_quality_procedure import create_procedure
from erpnext.quality_management.doctype.quality_goal.test_quality_goal import create_unit
from erpnext.quality_management.doctype.quality_goal.test_quality_goal import create_goal

class TestQualityReview(unittest.TestCase):

	def test_quality_review(self):
		create_procedure()
		create_unit()
		create_goal()
		test_create_review = create_review()
		test_get_review = get_review()
		self.assertEquals(test_create_review.name, test_get_review.name)

def create_review():
	review = frappe.get_doc({
		"doctype": "Quality Review",
		"goal": "_Test Quality Goal",
		"procedure": "_Test Quality Procedure",
		"scope": "Company",
		"date": ""+ frappe.utils.nowdate() +"",
		"values": [
			{
				"objective": "_Test Quality Objective",
				"target": "100",
				"achieved": "100",
				"unit": "_Test UOM"
			}
		]
	})
	review_exist = frappe.get_list("Quality Review", filters={"goal": "_Test Quality Goal"}, limit=1)
	if len(review_exist) == 0:
		review.insert()
		return review
	else:
		return review_exist[0]

def get_review():
	review = frappe.get_list("Quality Review", filters={"goal": "_Test Quality Goal"}, limit=1)
	return review[0]