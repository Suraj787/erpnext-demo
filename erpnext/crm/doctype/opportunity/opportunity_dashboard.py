from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'prevdoc_docname',
		'non_standard_fieldnames': {
			'Supplier Quotation': 'opportunity',
			'Quotation': 'opportunity'
		},
		'transactions': [
			{
				'items': ['Quotation', 'Supplier Quotation']
			},
		]
	}