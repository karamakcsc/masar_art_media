frappe.ui.form.on('Sales Order', {
    onload: function(frm) {
        if (!frm.doc.__islocal) {
            return;
        }
        if (frm.doc.custom_units && frm.doc.custom_units.length) {
            return;
        }
        frappe.db.get_list('Production Unit', {
            filters: {
                default: 1,
                enabled: 1
            },
            fields: ['name', 'description']
        }).then(units => {
            units.forEach(unit => {
                let row = frm.add_child('custom_units');
                row.production_unit = unit.name;
                row.description = unit.description;
            });
            frm.refresh_field('custom_units');
        });
    }
});