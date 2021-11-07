frappe.pages['hr-dashboard'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'HR Dashboard',
		single_column: true
	});

	page.main.html(frappe.render_template("hr_dashboard", {}));
	var employee_filter = frappe.ui.form.make_control({
		parent: page.main.find(".employee-filter"),
		df: {
			fieldtype: "Link",
			options: "Employee",
			fieldname: "employee",
			placeholder: __("Employee"),
			change: function(){
				console.log(employee_filter)
				if (employee_filter.get_value() != ""){
					let filters = {
						"employee":employee_filter.get_value(),
						"department":department_filter.get_value(),
						"leave_type":leave_type_filter.get_value(),	
					}
					get_init_data(filters);
					event.stopImmediatePropagation();
				}
				else {
					get_init_data({});
				}

			}
		},
		only_input: true,
	});
	var department_filter = frappe.ui.form.make_control({
		parent: page.main.find(".department-filter"),
		df: {
			fieldtype: "Link",
			options: "Department",
			fieldname: "department",
			placeholder: __("Department"),
			change: function(){
				console.log(department_filter)
				if (department_filter.get_value() != ""){
					let filters = {
						"employee":employee_filter.get_value(),
						"department":department_filter.get_value(),
						"leave_type":leave_type_filter.get_value(),	
					}
					get_init_data(filters);
					event.stopImmediatePropagation();
				}
				else {
					get_init_data({});

				}
			}
		},
		only_input: true,
	});
	var leave_type_filter = frappe.ui.form.make_control({
		parent: page.main.find(".leave-type-filter"),
		df: {
			fieldtype: "Link",
			options: "Leave Type",
			fieldname: "leave_type",
			placeholder: __("Leave Type"),
			change: function(){
				console.log(leave_type_filter)
				if (leave_type_filter.get_value() != ""){
					let filters = {
						"employee":employee_filter.get_value(),
						"department":department_filter.get_value(),
						"leave_type":leave_type_filter.get_value(),	
					}
					get_init_data(filters);
					event.stopImmediatePropagation();
				}
				else {	
					get_init_data({});
				}
			}
		},
		only_input: true,
	});
	
	var reset_filter = frappe.ui.form.make_control({
		parent: page.main.find(".reset-filter"),
		df: {
			fieldtype: "Button",
			fieldname: "reset_button",
			placeholder: __("Reset"),
			label: __("Reset"),
			change: function(){
				get_init_data({});
			}
		},
		only_input: true,
	});

	employee_filter.refresh();
	department_filter.refresh();
	leave_type_filter.refresh();
	reset_filter.refresh();
	
	get_init_data({});
	 
}

	
get_init_data = function (filters){
	setTimeout(function () {

		//Labels 
		get_all_employee();
		get_latest_leaves(filters);
		// Donut
		chart_donut_get_data("attendance",filters);
		chart_donut_get_data("grade",filters);
		chart_donut_get_data("nationality",filters);
		chart_donut_get_data("gender",filters);
		chart_line_get_data("leaves",filters);
	   
	  }, 400);
}
get_all_employee = function (){
	frappe.call({
			method: "erpnext.hr.page.hr_dashboard.hr_dashboard.get_employee",
			args: {
				nationality: "All"
			},
			callback: function(r) {
				if(r.message) {
					$("#all_employee").text(r.message[0])
					$("#saudi_employee").text(r.message[1])
					$("#none_saudi_employee").text(r.message[2])
				}
			}
	})
}

get_latest_leaves = function (filters){
	data = "No Data"
	 $("#latest-leaves").text("");
	frappe.call({
			method: "erpnext.hr.page.hr_dashboard.hr_dashboard.get_latest_leaves",
			args: {
				nationality: "All",
				args:filters
			},
			callback: function(r) {
				if(r.message) {
					console.log(r.message)
					for (let elem in r.message) {  
					  var markup = "<tr> <td>"+r.message[elem][0]+
					  "</td><td>"+r.message[elem][1]+
					  "</td> <td>"+r.message[elem][2]+
					  "</td> <td>"+r.message[elem][3]+
					  "</td> <td>"+r.message[elem][4]+
					  "</td> <td>"+r.message[elem][5]+
					  "</td> </tr>";	
					  $("#latest-leaves").append(markup);
					}
				}
			}
	})
	
}


chart_donut_get_data = function(label,filters){
	let data =[]
	
	frappe.call({
			method: "erpnext.hr.page.hr_dashboard.hr_dashboard.get_"+label,
			args: {
				args:filters
			},
			callback: function(r) {
				if(r.message) {
					$('#morris-donut-chart-'+label).empty();
					let data = r.message
					for (let elem in data) {
						data[elem]["label"] = __(data[elem]["label"])
					}
					Morris.Donut({
						element: 'morris-donut-chart-'+label,
						data: r.message,
						colors: [
							'#6156ce',
							'#00d1c1',
							'#EF6C00'
						],
						resize: true
					});
				}
			}
	})
	return data

}
chart_line_get_data = function(label,filters){
	let data =[]
	frappe.call({
			method: "erpnext.hr.page.hr_dashboard.hr_dashboard.get_"+label,
			args: {
				args:filters
			},
			callback: function(r) {
				$("#morris-line-chart-"+label).empty();
				if(r.message) {
					console.log(r.message)
					// Line Chart
					Morris.Line({
						// ID of the element in which to draw the chart.
						element: 'morris-line-chart-'+label,
						// Chart data records -- each entry in this array corresponds to a point on
						// the chart.
						data: r.message,
						// The name of the data record attribute that contains x-leavess.
						xkey: 'd',
						// A list of names of data record attributes that contain y-leavess.
						ykeys: [label],
						// Labels for the ykeys -- will be displayed when you hover over the
						// chart.
						labels: [label],
						// Disables line smoothing
						lineColors: ['#00d1c1'],
						smooth: false,
						resize: true
					});
				}
			}
	})
	return data

}
