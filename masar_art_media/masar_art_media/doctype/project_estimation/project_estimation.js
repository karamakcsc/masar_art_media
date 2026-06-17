// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Project Estimation', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Quotation'), function() {
                frappe.model.open_mapped_doc({
                    method: "masar_art_media.masar_art_media.doctype.project_estimation.project_estimation.make_quotation",
                    frm: frm,
                    freeze_message: __("Creating Quotation..."),
                });
            }, __('Create'));
        }
    },
    profit_margin_percentage: function(frm) {
        frm.trigger('calculate_totals');
    },
    calculate_totals: function(frm) {
        let total = 0;
        let total_qty = 0;
        (frm.doc.items || []).forEach(row => {
            total += row.amount || 0;
            total_qty += row.qty || 0;
        });
        frm.set_value('total', total);
        let profit_pct = frm.doc.profit_margin_percentage || 0;
        let profit_amt = total * (profit_pct / 100);
        let final_price = total + profit_amt;
        frm.set_value('profit_amount', profit_amt);
        frm.set_value('final_selling_price', final_price);
        frm.set_value('total_qty' , total_qty);
    }
});
frappe.ui.form.on('Project Estimation Item', {
    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', (row.qty || 0) * (row.rate || 0));
        frm.trigger('calculate_totals');
    },
    rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', (row.qty || 0) * (row.rate || 0));
        frm.trigger('calculate_totals');
    },
    items_remove: function(frm) {
        frm.trigger('calculate_totals');
    }
});
