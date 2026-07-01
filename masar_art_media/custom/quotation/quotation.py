import frappe


def before_submit(doc, method=None):
	missing = []
	for item in doc.items:
		has_submitted = frappe.db.exists(
			"Costing Sheet",
			{"quotation_item": item.name, "docstatus": 1},
		)
		if not has_submitted:
			missing.append(f"Row {item.idx}: <b>{item.item_name or item.item_code}</b>")

	if missing:
		frappe.throw(
			"The following items do not have a submitted Costing Sheet:<br><br>"
			+ "<br>".join(missing),
			title="Missing Costing Sheets",
		)


def before_cancel(doc, method=None):
	"""Cancel all submitted Costing Sheets linked to this Quotation."""
	doc.flags.ignore_links = True
	submitted_sheets = frappe.get_all(
		"Costing Sheet",
		filters={"quotation": doc.name, "docstatus": 1},
		pluck="name",
	)
	for i in doc.items: 
		i.custom_project_estimation = ""
	frappe.flags.cancelling_quotation = doc.name
	try:
		for cs_name in submitted_sheets:
			cs_doc = frappe.get_doc("Costing Sheet", cs_name)
			cs_doc.flags.ignore_links = True
			cs_doc.cancel()
	finally:
		frappe.flags.cancelling_quotation = None
	



def before_insert(doc, method=None):
	for item in doc.items:
		item.custom_project_estimation = ""
		item.custom_costing_amount = 0
		item.rate = 0 