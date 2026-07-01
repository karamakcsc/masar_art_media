from frappe import _

def get_dashboard_data(data):
    data["transactions"].append({
        "label": _("Costing"),
        "items": ["Costing Sheet"]
    })
    if not data.get("non_standard_fieldnames"):
        data["non_standard_fieldnames"] = {}
    data["non_standard_fieldnames"]["Costing Sheet"] = "quotation"
    return data