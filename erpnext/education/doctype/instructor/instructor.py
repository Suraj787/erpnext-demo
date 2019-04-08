# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import set_name_by_naming_series

class Instructor(Document):
	def autoname(self):
		naming_method = frappe.db.get_value("Education Settings", None, "instructor_created_by")
		if not naming_method:
			frappe.throw(_("Please setup Instructor Naming System in Education > Education Settings"))
		else:
			if naming_method == 'Naming Series':
				set_name_by_naming_series(self)
			elif naming_method == 'Employee Number':
				if not self.employee:
					frappe.throw(_("Please select Employee"))
				self.name = self.employee
			elif naming_method == 'Full Name':
				self.name = self.instructor_name
