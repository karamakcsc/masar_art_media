import frappe , time
from frappe import _
from frappe.utils import flt, now_datetime, get_datetime , getdate

def validate(self , method):
    frappe.enqueue(update_parent_task_status_and_progress,self=self)
def before_validate(self , method):
    if self.parent_task:
        parent_doc = frappe.get_doc("Task", self.parent_task)
        if getdate(self.exp_end_date) > getdate(parent_doc.exp_end_date):
            parent_doc.exp_end_date = self.exp_end_date
            parent_doc.flags.from_backend_automation = True
            parent_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
    
    
                    
def update_parent_task_status_and_progress(self):
    time.sleep(0.5)
    frappe.db.commit()
    if not self.parent_task:
        return
    child_tasks = frappe.get_all(
        "Task",
        filters={"parent_task": self.parent_task,"status": ["!=", "Cancelled"]},
        fields=["name","status","progress", "completed_on"]
    )
    if not child_tasks:
        child_tasks = frappe.get_all(
        "Task",
        filters={"parent_task": self.parent_task,"status": ["=", "Cancelled"]},
        fields=["name","status","progress", "completed_on"]
    )
        if child_tasks:
            parent_doc = frappe.get_doc("Task", self.parent_task)
            parent_doc.flags.from_backend_automation = True
            parent_doc.status = "Cancelled"
            parent_doc.progress = 0.0
            parent_doc.completed_by = None
            parent_doc.completed_on = None
            parent_doc.save(ignore_permissions=True)
            if parent_doc.project:
                project_doc = frappe.get_doc("Project", parent_doc.project)
                if project_doc.status != "Cancelled":
                    project_doc.status = "Cancelled"
                    project_doc.save(ignore_permissions=True)
                    frappe.msgprint(_(f"Project <b>{project_doc.name}</b> has been automatically marked <b>Cancelled</b>."))
            return
    total_children = len(child_tasks)
    total_progress = 0.0
    completed_count = 0
    has_working_children = False
    latest_completed_on = None
    for child in child_tasks:
        child_status = child.status
        child_progress = child.progress or 0
        child_completed_on = child.completed_on
        if child.name == self.name:
            child_status = self.status
            child_progress = self.progress or 0
            child_completed_on = self.completed_on
        total_progress += flt(child_progress)
        if child_status == "Completed":
            completed_count += 1
            if child_completed_on:
                child_completed_on = get_datetime(child_completed_on)
                if (latest_completed_on is None or child_completed_on > latest_completed_on):
                    latest_completed_on = child_completed_on
        elif child_status in ["Working", "Pending Review"]:
            has_working_children = True
    calculated_progress = flt(total_progress / total_children, 2)
    if completed_count == total_children:
        parent_status = "Completed"
    elif has_working_children or completed_count > 0:
        parent_status = "Working"
    else:
        parent_status = "Open"
    parent_doc = frappe.get_doc("Task", self.parent_task)
    parent_doc.flags.from_backend_automation = True
    parent_doc.progress = calculated_progress
    parent_doc.status = parent_status
    if parent_status == "Completed":
        parent_doc.completed_by = None
        parent_doc.completed_on = latest_completed_on or now_datetime()
    else:
        parent_doc.completed_by = None
        parent_doc.completed_on = None
    parent_doc.save(ignore_permissions=True)
    if parent_doc.project:
        project_doc = frappe.get_doc("Project", parent_doc.project)
        if parent_status == "Completed" and project_doc.status != "Completed":
            project_doc.status = "Completed"
            project_doc.save(ignore_permissions=True)
            frappe.msgprint(_(f"Project <b>{project_doc.name}</b> has been automatically marked <b>Completed</b>."))
        elif parent_status != "Completed" and project_doc.status == "Completed":
            project_doc.status = "Open"
            project_doc.save(ignore_permissions=True)
            frappe.msgprint(_(f"Project <b>{project_doc.name}</b> has been reopened because tasks are active."))
        elif parent_doc.status == "Cancelled" and project_doc.status != "Cancelled":
            project_doc.status = "Cancelled"
            project_doc.save(ignore_permissions=True)
            frappe.msgprint(_(f"Project <b>{project_doc.name}</b> has been automatically marked <b>Cancelled</b>."))
