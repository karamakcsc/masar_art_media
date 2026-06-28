import frappe 
from frappe.utils import add_days , nowdate , flt
###
def on_submit(self , method):
    create_peroject_from_sales_order(self)
    check_repeat_rows_in_units(self)
    
def create_peroject_from_sales_order(self):
    estimated_costing =  frappe.db.sql(
        f"""SELECT 
                SUM(IFNULL(pei.rate * soi.qty, 0))  AS estimated_costing 
            FROM `tabSales Order` so 
            INNER JOIN `tabSales Order Item` soi ON so.name = soi.parent 
            INNER JOIN `tabQuotation Item` qi ON soi.quotation_item  = qi.name 
            INNER JOIN `tabProject Estimation Item` pei ON pei.name = qi.custom_pe_details 
            WHERE so.name = '{self.name}'"""
    )
    project = frappe.get_doc({
        'doctype': 'Project' , 
        'project_name': f'Project for {self.name} - {self.customer_name}',
        'status' : 'Open', 
        'sales_order' : self.name, 
        'company' : self.company,
        'estimated_costing' : flt(estimated_costing[0][0]) if estimated_costing else 0,
        'total_sales_amount' : self.grand_total,
        'percent_complete_method' : 'Task Progress',
        
    })
    project.insert(ignore_permissions = True)
    if len(self.custom_units) == 0:
        frappe.throw("No active Producation units found in the sales order. Please add at least one Producation unit to proceed.")
    parent_task = frappe.get_doc({
        "doctype": "Task",
        "subject": f"Order Execution: {project.name}",
        "project": project.name,
        "status": "Open",
        "expected_start_date": nowdate(),
        "is_group": 1
    })
    parent_task.flags.from_backend_automation = True
    parent_task.insert(ignore_permissions=True)
    
    for unit in self.custom_units:
        child_task = frappe.get_doc({
            "doctype": "Task",
            "subject": f"{unit.production_unit}",
            "project": project.name,
            "parent_task": parent_task.name,
            "status": "Open",
            "expected_start_date": nowdate(),
            "expected_end_date": add_days(nowdate(), 7),
            })
        child_task.insert(ignore_permissions=True)
    for item in self.items:
        item.project = project.name 
    self.db_update_all()  
    frappe.msgprint(
        f"Project <b>{project.name}</b> successfully generated! "
        f"Created Parent Task <b>{parent_task.name}</b> with {len(self.custom_units)} nested Producation unit tasks."
    )
    
def check_repeat_rows_in_units(self):
    seen_units = list()
    for unit in self.custom_units:
        if unit.production_unit in seen_units:
            frappe.throw(f"Duplicate Producation unit found: <b>{unit.production_unit}</b>. Please ensure each Producation unit is unique.")
        seen_units.append(unit.production_unit)