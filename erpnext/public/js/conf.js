// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide('erpnext');

// add toolbar icon
$(document).bind('toolbar_setup', function() {
	frappe.app.name = "ERPNext";

	frappe.help_feedback_link = '<p><a class="text-muted" \
		href="https://discuss.erpnext.com">Feedback</a></p>'


	$('.navbar-home').html('<img class="erpnext-icon" src="'+
			frappe.urllib.get_base_url()+'/assets/erpnext/images/erp-icon.svg" />');

	$('[data-link="docs"]').attr("href", "https://erpnext.com/docs")
	$('[data-link="issues"]').attr("href", "https://github.com/frappe/erpnext/issues")


	// default documentation goes to erpnext
	// $('[data-link-type="documentation"]').attr('data-path', '/erpnext/manual/index');

	// additional help links for erpnext
	var $help_menu = $('.dropdown-help ul .documentation-links');
	$('<li><a data-link-type="forum" href="https://erpnext.com/docs/user/manual" \
		target="_blank">'+__('Documentation')+'</a></li>').insertBefore($help_menu);
	$('<li><a data-link-type="forum" href="https://discuss.erpnext.com" \
		target="_blank">'+__('User Forum')+'</a></li>').insertBefore($help_menu);
	$('<li class="gitter-chat-link"><a href="https://gitter.im/frappe/erpnext" \
		target="_blank">'+__('Gitter Chat')+'</a></li>').insertBefore($help_menu);
	$('<li><a href="https://github.com/frappe/erpnext/issues" \
		target="_blank">'+__('Report an Issue')+'</a></li>').insertBefore($help_menu);

});



// doctypes created via tree
$.extend(frappe.create_routes, {
	"Customer Group": "Tree/Customer Group",
	"Territory": "Tree/Territory",
	"Item Group": "Tree/Item Group",
	"Sales Person": "Tree/Sales Person",
	"Account": "Tree/Account",
	"Cost Center": "Tree/Cost Center"
});

// preferred modules for breadcrumbs
$.extend(frappe.breadcrumbs.preferred, {
	"Item Group": "Stock",
	"Customer Group": "Selling",
	"Supplier Group": "Buying",
	"Territory": "Selling",
	"Sales Person": "Selling",
	"Sales Partner": "Selling",
	"Brand": "Selling"
});
