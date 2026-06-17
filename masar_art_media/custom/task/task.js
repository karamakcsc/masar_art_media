frappe.ui.form.on('Task', {
    refresh: function(frm) {
        if (frm.doc.is_group) {
            // if (frappe.session.user !== 'Administrator') {
                frm.disable_form();
                frm.dashboard.add_comment(__('This is an automated Parent Task container. Edits are restricted to the Administrator.'), 'orange');
            // }
        }
        if (frm.doc.project) {
            frm.add_custom_button(__('Request Materials'), function() {
                frappe.model.with_doctype('Material Request', function() {
                    let mr = frappe.model.get_new_doc('Material Request');
                    mr.loading_status = "Draft";
                    mr.transaction_date = frappe.datetime.nowdate();
                    let row = frappe.model.add_child(mr, 'items');
                    row.project = frm.doc.project;
                    frappe.set_route('Form', 'Material Request', mr.name);
                });
            }, __('Actions'));
        }
    },
    status: function(frm) {
        if (!frm.doc.is_group) {
            if (frm.doc.status === 'Completed') {
                frm.set_value('completed_by', frappe.session.user);
                frm.set_value('completed_on', frappe.datetime.now_datetime());
            } else {
                frm.set_value('completed_by', '');
                frm.set_value('completed_on', '');
            }
        }
    }
});