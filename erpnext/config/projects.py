from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Projects"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Project",
					"description": _("Project master."),
				},
				# {
				# 	"type": "doctype",
				# 	"name": "Planning",
				# 	"description": _("Project Planning."),
				# },
				{
					"type": "doctype",
					"name": "Task",
					"description": _("Project activity / task."),
				},
				{
					"type": "doctype",
					"name": "Project Charter",
					"description": _("Project Charter."),
				},
				{
					"type": "report",
					"route": "List/Task/Gantt",
					"doctype": "Task",
					"name": "Gantt Chart",
					"description": _("Gantt chart of all tasks.")
				},
			]
		},
		# {
		# 	"label": _("Time Tracking"),
		# 	"items": [
		# 		{
		# 			"type": "doctype",
		# 			"name": "Timesheet",
		# 			"description": _("Timesheet for tasks."),
		# 		},
		# 		{
		# 			"type": "doctype",
		# 			"name": "Activity Type",
		# 			"description": _("Types of activities for Time Logs"),
		# 		},
		# 		{
		# 			"type": "doctype",
		# 			"name": "Activity Cost",
		# 			"description": _("Cost of various activities"),
		# 		},
		# 	]
		# },
		{
			"label": _("Projects Control"),
			"items": [
				{
					"type": "doctype",
					"name": "Project Billing Control",
					"label": _("Projects Billing Control"),
					"description": _("Project Billing Control."),
				},
				{
					"type": "doctype",
					"name": "Projects Procurement Control",
					"label": _("Projects Procurement Control"),
					"description": _("Projects Procurement Control."),
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
					"name": "Daily Timesheet Summary",
					"doctype": "Timesheet"
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Project wise Stock Tracking",
					"doctype": "Project"
				},
			]
		},
		{
			"label": _("Help"),
			"icon": "fa fa-facetime-video",
			"items": [
				{
					"type": "help",
					"label": _("Managing Projects"),
					"youtube_id": "egxIGwtoKI4"
				},
			]
		},
	]
