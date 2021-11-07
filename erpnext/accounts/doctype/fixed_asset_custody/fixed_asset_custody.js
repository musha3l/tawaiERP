// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt


cur_frm.add_fetch("fixed_asset", "image", "image");
cur_frm.fields_dict['fixed_asset'].get_query = function(doc) {
    return {
        filters: [
            ['status', 'not in', 'Scrapped, Sold'],
            ['docstatus', '=', '1']
        ]
    }
}
cur_frm.fields_dict['employee'].get_query = function(doc) {
    return {
        filters: {
            "status": "Active"
        }
    }
}

frappe.ui.form.on('Fixed Asset Custody', {
    refresh: function(frm) {
    }
});
