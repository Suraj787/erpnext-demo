// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student', {
	setup: function(frm) {
		frm.add_fetch("guardian", "guardian_name", "guardian_name");
		frm.add_fetch("student", "title", "full_name");
		frm.add_fetch("student", "gender", "gender");
		frm.add_fetch("student", "date_of_birth", "date_of_birth");

		frm.set_query("student", "siblings", function(doc, cdt, cdn) {
			return {
				"filters": {
					"name": ["!=", doc.name]
				}
			};
		})
	},
	refresh: function(frm) {
		if(!frm.is_new()) {

			// custom buttons
			frm.add_custom_button(__('Accounting Ledger'), function() {
				frappe.set_route('query-report', 'General Ledger',
					{party_type:'Student', party:frm.doc.name});
			});
		}
	}
});
