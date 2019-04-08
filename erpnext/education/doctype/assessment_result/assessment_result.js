// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Assessment Result", {
	onload: function(frm) {
		frm.set_query('assessment_plan', function(){
			return {
				filters: {
					docstatus: 1
				}
			};
		});
	},

	assessment_plan: function(frm) {
		if (frm.doc.assessment_plan) {
			frappe.call({
				method: "erpnext.education.api.get_assessment_details",
				args: {
					assessment_plan: frm.doc.assessment_plan
				},
				callback: function(r) {
					if (r.message) {
						frm.doc.details = [];
						$.each(r.message, function(i, d) {
							var row = frappe.model.add_child(frm.doc, "Assessment Result Detail", "details");
							row.assessment_criteria = d.assessment_criteria;
							row.maximum_score = d.maximum_score;
						});
					}
					refresh_field("details");
				}
			});
		}
	}
});

frappe.ui.form.on("Assessment Result Detail", {
	score: function(frm, cdt, cdn) {
		var d  = locals[cdt][cdn];

		if(!d.maximum_score || !frm.doc.grading_scale) {
			d.score = "";
			frappe.throw(__("Please fill in all the details to generate Assessment Result."));
		}

		if (d.score > d.maximum_score) {
			frappe.throw(__("Score cannot be greater than Maximum Score"));
		}
		else {
			frappe.call({
				method: "erpnext.education.api.get_grade",
				args: {
					grading_scale: frm.doc.grading_scale,
					percentage: ((d.score/d.maximum_score) * 100)
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "grade", r.message);
					}
				}
			});
		}
	}
});