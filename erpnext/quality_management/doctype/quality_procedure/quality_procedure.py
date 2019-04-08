# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.nestedset import NestedSet
from frappe import _

class QualityProcedure(NestedSet):
	nsm_parent_field = 'parent_quality_procedure'

	def before_save(self):
		for data in self.procedure_step:
			if data.procedure == 'Procedure' and data.procedure_name:
				data.step = data.procedure_name
				doc = frappe.get_doc("Quality Procedure", data.procedure_name)
				if(doc.parent_quality_procedure):
					frappe.throw(_("'"+ data.procedure_name +"' already has a Parent Procedure '"+ doc.parent_quality_procedure +"'"))
				self.is_group = 1

	def on_update(self):
		self.set_parent()

	def after_insert(self):
		self.set_parent()

	def on_trash(self):
		if self.parent_quality_procedure:
			doc = frappe.get_doc("Quality Procedure", self.parent_quality_procedure)
			for data in doc.procedure_step:
				if data.procedure_name == self.name:
					doc.procedure_step.remove(data)
					doc.save()
			flag_is_group = 0
			doc.load_from_db()
			for data in doc.procedure_step:
				if data.procedure == "Procedure":
					flag_is_group = 1
			if flag_is_group == 0:
				doc.is_group = 0
				doc.save()

	def set_parent(self):
		for data in self.procedure_step:
			if data.procedure == 'Procedure' and data.procedure_name:
				doc = frappe.get_doc("Quality Procedure", data.procedure_name)
				doc.parent_quality_procedure = self.name
				doc.save()

@frappe.whitelist()
def get_children(doctype, parent=None, parent_quality_procedure=None, is_root=False):
	if parent is None or parent == "All Quality Procedures":
		parent = ""
	return frappe.get_all(doctype, fields=["name as value", "is_group as expandable"], filters={"parent_quality_procedure": parent})

@frappe.whitelist()
def add_node():
	from frappe.desk.treeview import make_tree_args
	args = frappe.form_dict
	args = make_tree_args(**args)
	if args.parent_quality_procedure == 'All Quality Procedures':
		args.parent_quality_procedure = None
	frappe.get_doc(args).insert()