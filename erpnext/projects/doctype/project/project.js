// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
frappe.ui.form.on("Project", {
	setup: function (frm) {
		frm.set_indicator_formatter('title',
			function (doc) {
				let indicator = 'orange';
				if (doc.status == 'Overdue') {
					indicator = 'red';
				} else if (doc.status == 'Cancelled') {
					indicator = 'dark grey';
				} else if (doc.status == 'Completed') {
					indicator = 'green';
				}
				return indicator;
			}
		);
	},


	onload: function (frm) {
		var so = frappe.meta.get_docfield("Project", "sales_order");
		so.get_route_options_for_new_doc = function (field) {
			if (frm.is_new()) return;
			return {
				"customer": frm.doc.customer,
				"project_name": frm.doc.name
			}
		}

		frm.set_query('customer', 'erpnext.controllers.queries.customer_query');

		frm.set_query("user", "users", function () {
			return {
				query: "erpnext.projects.doctype.project.project.get_users_for_project"
			}
		});

		// sales order
		frm.set_query('sales_order', function () {
			var filters = {
				'project': ["in", frm.doc.__islocal ? [""] : [frm.doc.name, ""]]
			};

			if (frm.doc.customer) {
				filters["customer"] = frm.doc.customer;
			}

			return {
				filters: filters
			}
		});

		if (frappe.model.can_read("Task")) {
			frm.add_custom_button(__("Gantt Chart"), function () {
				frappe.route_options = {
					"project": frm.doc.name
				};
				frappe.set_route("List", "Task", "Gantt");
			});

			frm.add_custom_button(__("Kanban Board"), () => {
				frappe.call('erpnext.projects.doctype.project.project.create_kanban_board_if_not_exists', {
					project: frm.doc.project_name
				}).then(() => {
					frappe.set_route('List', 'Task', 'Kanban', frm.doc.project_name);
				});
			});
		}
	},

	refresh: function (frm) {
		if (frm.doc.__islocal) {
			frm.web_link && frm.web_link.remove();
		} else {
			frm.add_web_link("/projects?project=" + encodeURIComponent(frm.doc.name));

			frm.trigger('show_dashboard');
		}
		frm.events.set_buttons(frm);
	},

	set_buttons: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Completed'), () => {
				frm.events.set_status(frm, 'Completed');
			}, __('Set Status'));

			frm.add_custom_button(__('Cancelled'), () => {
				frm.events.set_status(frm, 'Cancelled');
			}, __('Set Status'));
		}
	},

	set_status: function(frm, status) {
		frappe.confirm(__('Set Project and all Tasks to status {0}?', [status.bold()]), () => {
			frappe.xcall('erpnext.projects.doctype.project.project.set_project_status',
				{project: frm.doc.name, status: status}).then(() => { /* page will auto reload */ });
		});
	},

	tasks_refresh: function (frm) {
		var grid = frm.get_field('tasks').grid;
		grid.wrapper.find('select[data-fieldname="status"]').each(function () {
			if ($(this).val() === 'Open') {
				$(this).addClass('input-indicator-open');
			} else {
				$(this).removeClass('input-indicator-open');
			}
		});
	},
});

frappe.ui.form.on("Project Task", {
	edit_task: function(frm, doctype, name) {
		var doc = frappe.get_doc(doctype, name);
		if(doc.task_id) {
			frappe.set_route("Form", "Task", doc.task_id);
		} else {
			frappe.msgprint(__("Save the document first."));
		}
	},

	edit_timesheet: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		frappe.route_options = {"project": frm.doc.project_name, "task": child.task_id};
		frappe.set_route("List", "Timesheet");
	},

	make_timesheet: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		frappe.model.with_doctype('Timesheet', function() {
			var doc = frappe.model.get_new_doc('Timesheet');
			var row = frappe.model.add_child(doc, 'time_logs');
			row.project = frm.doc.project_name;
			row.task = child.task_id;
			frappe.set_route('Form', doc.doctype, doc.name);
		})
	},

	status: function(frm, doctype, name) {
		frm.trigger('tasks_refresh');
	},
});
