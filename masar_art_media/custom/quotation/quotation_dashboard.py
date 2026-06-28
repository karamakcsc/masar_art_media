from frappe import _


def get_dashboard_data(data):
    data["transactions"].append({
        "label": _("Reference"),
        "items": ["Project Estimation"]
    })

    if not data.get("internal_links"):
        data["internal_links"] = {}

    data["internal_links"]["Project Estimation"] = ["items", "custom_project_estimation"]

    return data
