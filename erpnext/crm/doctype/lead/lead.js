// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext");
cur_frm.email_field = "email_id";

erpnext.LeadController = frappe.ui.form.Controller.extend({
	setup: function() {
		this.frm.fields_dict.customer.get_query = function(doc, cdt, cdn) {
			return { query: "erpnext.controllers.queries.customer_query" } }
	},

	onload: function() {

		if(cur_frm.fields_dict.lead_owner.df.options.match(/^User/)) {
			cur_frm.fields_dict.lead_owner.get_query = function(doc, cdt, cdn) {
				return { query: "frappe.core.doctype.user.user.user_query" }
			}
		}

		if(cur_frm.fields_dict.contact_by.df.options.match(/^User/)) {
			cur_frm.fields_dict.contact_by.get_query = function(doc, cdt, cdn) {
				return { query: "frappe.core.doctype.user.user.user_query" } }
		}
	},

	refresh: function() {
		var doc = this.frm.doc;
		erpnext.toggle_naming_series();
		frappe.dynamic_link = {doc: doc, fieldname: 'name', doctype: 'Lead'}

		if(!doc.__islocal && doc.__onload && !doc.__onload.is_customer) {
			this.frm.add_custom_button(__("Customer"), this.create_customer, __('Create'));
			this.frm.add_custom_button(__("Opportunity"), this.create_opportunity, __('Create'));
			this.frm.add_custom_button(__("Quotation"), this.make_quotation, __('Create'));
		}

		if(!this.frm.doc.__islocal) {
			frappe.contacts.render_address_and_contact(cur_frm);
		} else {
			frappe.contacts.clear_address_and_contact(cur_frm);
		}
	},

	create_customer: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.crm.doctype.lead.lead.make_customer",
			frm: cur_frm
		})
	},

	create_opportunity: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.crm.doctype.lead.lead.make_opportunity",
			frm: cur_frm
		})
	},

	make_quotation: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.crm.doctype.lead.lead.make_quotation",
			frm: cur_frm
		})
	},

	organization_lead: function() {
		if (this.frm.doc.organization_lead == 1) {
			this.frm.set_df_property('company_name', 'reqd', 1);
		} else {
			this.frm.set_df_property('company_name', 'reqd', 0);
		}
	},

	company_name: function() {
		if (this.frm.doc.organization_lead == 1) {
			this.frm.set_value("lead_name", this.frm.doc.company_name);
		}
	},

	contact_date: function() {
		if (this.frm.doc.contact_date) {
			let d = moment(this.frm.doc.contact_date);
			d.add(1, "hours");
			this.frm.set_value("ends_on", d.format(frappe.defaultDatetimeFormat));
		}
	}
});

$.extend(cur_frm.cscript, new erpnext.LeadController({frm: cur_frm}));
