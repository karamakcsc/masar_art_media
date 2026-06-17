import frappe
from frappe import _

def validate_mandatory_project(self, method):
    header_project = getattr(self, "project", None)
    if not header_project:
        if hasattr(self, "items") and self.items:
            for index, item in enumerate(self.items, start=1):
                if not getattr(item, "project", None):
                    frappe.throw(
                        msg=_(f"Row #{index}: <b>Project</b> is mandatory to trace project costing accurately!"),
                        title=_("Missing Project Assignment")
                    )
        else:
            frappe.throw(
                msg=_("Please assign a <b>Project</b> link to this selfument to track its financial entry."),
                title=_("Missing Project Assignment")
            )