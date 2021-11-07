// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Assets Barcode', {
	refresh: function(frm) {
		refresh_fields(frm);
	},
	get_assets:function(frm){
		if(frm.doc.empty_barcode_table == 1){
			frm.set_value("assets_barcode_details",[]);
		}
		if(frm.doc.generate_by == "Asset" && frm.doc.asset){
			// frm.set_value("assets_barcode_details",[])
			var asset = frm.add_child("assets_barcode_details",[]);
			asset.asset_name = frm.doc.asset;

			frappe.call({
				method:"frappe.client.get_value",
				args: {
					doctype:"Asset",
					filters: {
						name:asset.asset_name
					},
					fieldname:["barcode_img", "name"]
				}, 
				callback: function(r) { 
					console.log(r);
					if(r.message){
						asset.barcode_img = r.message.barcode_img;
						frm.refresh_field("assets_barcode_details")
						frm.save();
					}
				}
			})
		}
		else if(frm.doc.generate_by == "Category" && frm.doc.asset_category ){
			load_barcode_cat(frm,frm.doc.asset_category);
		}else if(frm.doc.generate_by == "All" ){
			load_barcode_cat(frm,"All");
		}

	},
	generate_by:function(frm){
		refresh_fields(frm);
	}
});

function load_barcode_cat(frm,asset_category) {
	frappe.call({
		method:"load_barcode_cat",
		doc:cur_frm.doc,
		args: {
			"category":asset_category,
		},
		callback: function(r) { 
			// frm.set_value("assets_barcode_details",[])
			if(r.message){
				var assets_list = r.message;
				assets_list.forEach(asset => {
					var asset_child = frm.add_child("assets_barcode_details",[]);
					asset_child.asset_name = asset.name;
					asset_child.barcode_img = asset.barcode_img;
				});
				frm.refresh_field("assets_barcode_details")
				frm.save()
			}else{
				frappe.msgprint(__("This Asset Category has no following Assets!"))
			}
		}
	})

}
function refresh_fields(frm) {
	frm.set_df_property("get_assets","hidden",false);
	if(frm.doc.generate_by == "Asset"){
		frm.set_df_property("asset","hidden",false);
		frm.set_df_property("asset_category","hidden",true);
	}else if(frm.doc.generate_by == "Category"){
		frm.set_df_property("asset","hidden",true);
		frm.set_df_property("asset_category","hidden",false);
	}
	else if(frm.doc.generate_by == "All"){
		frm.set_df_property("get_assets","hidden",false);
		frm.set_df_property("asset","hidden",true);
		frm.set_df_property("asset_category","hidden",true);
	}else{
		frm.set_df_property("get_assets","hidden",true);
		frm.set_df_property("asset","hidden",true);
		frm.set_df_property("asset_category","hidden",true);
	
	}
}
frappe.ui.form.on("Assets Barcode Details", "asset_name", function(frm, doctype, name) {
	let asset_barcode_details = frappe.get_doc(doctype,name);
	let asset_name = asset_barcode_details.asset_name;
	let asset = frappe.get_doc("Asset",asset_name);

	frappe.call({
		method:"frappe.client.get_value",
		args: {
			doctype:"Asset",
			filters: {
				name:asset_name
			},
			fieldname:["barcode_img", "name"]
		}, 
		callback: function(r) { 
			console.log(r);
			if(r.message){
				frappe.model.set_value(doctype,name,"barcode_img",r.message.barcode_img)
				frm.save()

			}
		}
	})
	
})
