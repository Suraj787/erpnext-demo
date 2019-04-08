from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Sales Pipeline"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Lead",
					"description": _("Database of potential customers."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Opportunity",
					"description": _("Potential opportunities for selling."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Customer",
					"description": _("Customer database."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Contact",
					"description": _("All Contacts."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Communication",
					"description": _("Record of all communications of type email, phone, chat, visit, etc."),
				},
				{
					"type": "doctype",
					"name": "Lead Source",
					"description": _("Track Leads by Lead Source.")
				},
			]
		},
		{
			"label": _("Reports"),
			"icon": "fa fa-list",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Lead Details",
					"doctype": "Lead",
					"onboard": 1,
				},
				{
					"type": "page",
					"name": "sales-funnel",
					"label": _("Sales Funnel"),
					"icon": "fa fa-bar-chart",
					"onboard": 1,
				},
				{
					"type": "report",
					"name": "Prospects Engaged But Not Converted",
					"doctype": "Lead",
					"is_query_report": True,
					"onboard": 1,
				},
				{
					"type": "report",
					"name": "Minutes to First Response for Opportunity",
					"doctype": "Opportunity",
					"is_query_report": True,
					"dependencies": ["Opportunity"]
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Customer Addresses And Contacts",
					"doctype": "Contact",
					"dependencies": ["Customer"]
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Inactive Customers",
					"doctype": "Sales Order",
					"dependencies": ["Sales Order"]
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Campaign Efficiency",
					"doctype": "Lead",
					"dependencies": ["Lead"]
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Lead Owner Efficiency",
					"doctype": "Lead",
					"dependencies": ["Lead"]
				}
			]
		},
		{
			"label": _("Settings"),
			"icon": "fa fa-cog",
			"items": [
				{
					"type": "doctype",
					"label": _("Customer Group"),
					"name": "Customer Group",
					"icon": "fa fa-sitemap",
					"link": "Tree/Customer Group",
					"description": _("Manage Customer Group Tree."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"label": _("Territory"),
					"name": "Territory",
					"icon": "fa fa-sitemap",
					"link": "Tree/Territory",
					"description": _("Manage Territory Tree."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"label": _("Sales Person"),
					"name": "Sales Person",
					"icon": "fa fa-sitemap",
					"link": "Tree/Sales Person",
					"description": _("Manage Sales Person Tree."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Campaign",
					"description": _("Sales campaigns."),
				},
				{
					"type": "doctype",
					"name": "SMS Center",
					"description":_("Send mass SMS to your contacts"),
				},
				{
					"type": "doctype",
					"name": "SMS Log",
					"description":_("Logs for maintaining sms delivery status"),
				},
				{
					"type": "doctype",
					"name": "SMS Settings",
					"description": _("Setup SMS gateway settings")
				}
			]
		},
		{
			"label": _("Maintenance"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Maintenance Schedule",
					"description": _("Plan for maintenance visits."),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Maintenance Visit",
					"description": _("Visit report for maintenance call."),
				},
				{
					"type": "report",
					"name": "Maintenance Schedules",
					"is_query_report": True,
					"doctype": "Maintenance Schedule"
				},
				{
					"type": "doctype",
					"name": "Warranty Claim",
					"description": _("Warranty Claim against Serial No."),
				},
			]
		},
		# {
		# 	"label": _("Help"),
		# 	"items": [
		# 		{
		# 			"type": "help",
		# 			"label": _("Lead to Quotation"),
		# 			"youtube_id": "TxYX4r4JAKA"
		# 		},
		# 		{
		# 			"type": "help",
		# 			"label": _("Newsletters"),
		# 			"youtube_id": "muLKsCrrDRo"
		# 		},
		# 	]
		# },
	]
