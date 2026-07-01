// Copyright (c) 2026, KCSC and contributors
// For license information, please see license.txt

frappe.ui.form.on('Quotation', {
	refresh: function(frm) {
		// Re-render visible expanded rows when the form refreshes
		if (!frm.is_new()) {
			frm.fields_dict['items'].grid.grid_rows.forEach(grid_row => {
				if (grid_row.open_form_button && grid_row.grid_form) {
					_render_costing_sheet_button(frm, grid_row);
				}
			});
		}
	}
});

frappe.ui.form.on('Quotation Item', {
	form_render: function(frm, cdt, cdn) {
		if (frm.is_new()) return;

		let grid_row = frm.fields_dict['items'].grid.grid_rows_by_docname[cdn];
		if (!grid_row || !grid_row.grid_form) return;

		_render_costing_sheet_button(frm, grid_row);
	}
});

function _render_costing_sheet_button(frm, grid_row) {
	let cdn = grid_row.doc.name;
	let row = locals['Quotation Item'][cdn];
	if (!row) return;
	grid_row.grid_form.wrapper.find('.cs-action-section').remove();
	let has_cs = !!row.custom_project_estimation;
	let btn_text = has_cs ? __('Open Costing Sheet') : __('Create Costing Sheet');
	let btn_class = has_cs ? 'btn-default' : 'btn-primary';
	let cs_label = has_cs
		? `<span class="text-muted small ml-2">${row.custom_project_estimation}</span>`
		: '';

	let $section = $(`
		<div class="cs-action-section" style="margin: 6px 0 4px 0;">
			<button class="btn btn-xs ${btn_class}">${btn_text}</button>
			${cs_label}
		</div>
	`);
	$section.find('button').on('click', function() {
		if (has_cs) {
			frappe.set_route('Form', 'Costing Sheet', row.custom_project_estimation);
		} else {
			_create_costing_sheet(frm, row);
		}
	});
	let item_code_field = grid_row.grid_form.fields_dict['item_code'];
	if (item_code_field && item_code_field.$wrapper) {
		item_code_field.$wrapper.after($section);
	} else {
		grid_row.grid_form.wrapper.prepend($section);
	}
}

function _create_costing_sheet(frm, row) {
    const create_sheet = () => {
        frappe.call({
            method: 'masar_art_media.masar_art_media.doctype.costing_sheet.costing_sheet.make_costing_sheet',
            args: {
                quotation: frm.doc.name,
                quotation_item: row.name
            },
            freeze: true,
            freeze_message: __('Creating Costing Sheet...'),
            callback: function(r) {
                if (r.message) {
                    frappe.set_route('Form', 'Costing Sheet', r.message);
                }
            }
        });
    };

    if (frm.is_dirty()) {
        frm.save().then(() => {
            const saved_row = frm.doc.items.find(d => d.idx === row.idx);
            create_sheet(saved_row);
        });
    } else {
        create_sheet();
    }
}
