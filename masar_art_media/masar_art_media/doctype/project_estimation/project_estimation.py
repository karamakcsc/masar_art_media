# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe , json
from frappe.model.document import Document
from frappe.utils import flt , add_days , nowdate
from frappe.model.mapper import get_mapped_doc

class ProjectEstimation(Document):
    def validate(self):
        self.calculate_amounts_and_totals()

    def calculate_amounts_and_totals(self):
        total, total_qty = 0, 0 
        for i in self.items:
            i.amount = flt(i.qty) * flt(i.rate)
            total += flt(i.amount)
            i.final_selling_price = flt(i.rate) + (flt(i.rate) * (flt(self.profit_margin_percentage) /100 ))
            total_qty += flt(i.qty)
        self.total = total
        self.total_qty = total_qty
        profit_amount = total * (flt(self.profit_margin_percentage) / 100) 
        self.profit_amount = profit_amount
        self.final_selling_price = total + profit_amount


@frappe.whitelist()
def make_quotation(source_name, target_doc=None, args=None):
    if args is None:
        args = {}
    if isinstance(args, str):
        args = json.loads(args)
    def update_item(obj, target, source_parent):
        target.item_code = obj.item_code
        target.item_name = obj.item_name
        target.description = obj.description
        target.item_group = obj.item_group
        target.qty = obj.qty
        target.uom = frappe.db.get_value('Item', obj.item_code, 'stock_uom')
        target.rate = obj.final_selling_price
        target.ignore_pricing_rule = 1
        target.delivery_date = add_days(nowdate(), 1)
    def select_item(d):
        filtered_items = args.get("filtered_children", [])
        child_filter = d.name in filtered_items if filtered_items else True
        return child_filter

    doc = get_mapped_doc(
        "Project Estimation",
        source_name,
        {
            "Project Estimation": {
                "doctype": "Quotation",
                "field_map": {
                    "customer": "party_name",
                    "company" : "company", 
                    "posting_date" :  "transaction_date",
                    "SAL-QTN-.YYYY.-" : "naming_series",
                },
                "validation": {
                    "docstatus": ["=", 1],
                },
            },
            "Project Estimation Item": {
                "doctype": "Quotation Item",
                "field_map": {
                    "parent": "custom_project_estimation",
                    "name": "custom_pe_details",
                },
                "postprocess": update_item,
                "condition": lambda doc: select_item(doc),
            },
        },
        target_doc
    )

    return doc