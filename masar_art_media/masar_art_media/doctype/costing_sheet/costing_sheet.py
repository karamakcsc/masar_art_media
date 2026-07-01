# Copyright (c) 2026, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class CostingSheet(Document):
	def validate(self):
		self.validate_unique_items()
		self.calculate_amounts_and_totals()

	def before_submit(self):
		self.validate_unique_submission()

	def on_submit(self):
		if self.quotation and self.quotation_item:
			self._update_quotation_item()

	def on_cancel(self):
		if self.quotation_item:
			self._revert_quotation_item()

	def calculate_amounts_and_totals(self):
		total, total_qty = 0, 0
		for i in self.items:
			i.amount = flt(i.qty) * flt(i.rate)
			total += flt(i.amount)
			i.final_selling_price = flt(i.rate) + (flt(i.rate) * (flt(self.profit_margin_percentage) / 100))
			total_qty += flt(i.qty)
		self.total = total
		self.total_qty = total_qty
		profit_amount = total * (flt(self.profit_margin_percentage) / 100)
		self.profit_amount = profit_amount
		self.final_selling_price = total + profit_amount
	def validate_unique_items(self):
		seen_items = set()
		quotation_items_data = frappe.get_all(
			"Quotation Item",
			filters={"parent": self.quotation},
			fields=["item_code"],
		)
		quotation_items = [qi.item_code for qi in quotation_items_data]
		for item in self.items:
			if item.item_code in seen_items:
				frappe.throw(f"Duplicate item <b>{item.item_code}</b> found in Costing Sheet.")
			seen_items.add(item.item_code)
			if item.item_code  in quotation_items:
				frappe.throw(f"Item <b>{item.item_code}</b> is part of the Quotation <b>{self.quotation}</b>.")
	def validate_unique_submission(self):
		if not (self.quotation and self.quotation_item):
			return
		existing = frappe.db.get_value(
			"Costing Sheet",
			{
				"quotation_item": self.quotation_item,
				"docstatus": 1,
				"name": ("!=", self.name),
			},
			"name",
		)
		if existing:
			frappe.throw(
				f"A submitted Costing Sheet <b>{existing}</b> already exists for this quotation item. "
				"Cancel it before submitting a new one.",
				title="Duplicate Submission",
			)

	def _update_quotation_item(self):
		quotation = frappe.get_doc("Quotation", self.quotation)
		updated = False
		for item in quotation.items:
			if item.name == self.quotation_item:
				item.rate = self.final_selling_price
				item.amount = flt(item.rate) * flt(item.qty)
				item.custom_project_estimation = self.name
				updated = True
				break
		if updated:
			quotation.flags.ignore_permissions = True
			quotation.save()
			frappe.publish_realtime(
				"quotation_updated_from_costing_sheet",
				{
					"quotation": self.quotation
				}
			)
			frappe.msgprint(
				f"Rate updated on Quotation {self.quotation} to {self.final_selling_price}",
				alert=True,
			)
		quotation.reload()

	def _revert_quotation_item(self):
		current_cs = frappe.db.get_value(
			"Quotation Item", self.quotation_item, "custom_project_estimation"
		)
		if current_cs == self.name:
			frappe.db.set_value(
				"Quotation Item", self.quotation_item, "custom_project_estimation", ""
			)


@frappe.whitelist()
def make_costing_sheet(quotation, quotation_item):
	quotation_doc = frappe.get_doc("Quotation", quotation)
	qt_item = next((i for i in quotation_doc.items if i.name == quotation_item), None)
	if not qt_item:
		frappe.throw(f"Item row not found in Quotation {quotation}")
	existing_draft = frappe.db.get_value(
		"Costing Sheet",
		{"quotation": quotation, "quotation_item": quotation_item, "docstatus": 0},
		"name",
	)
	if existing_draft:
		return existing_draft
	cs = frappe.new_doc("Costing Sheet")
	cs.customer = quotation_doc.party_name
	cs.company = quotation_doc.company
	cs.quotation = quotation
	cs.quotation_item = quotation_item
	cs.sales_item_code = qt_item.item_code
	cs.item_description = qt_item.description or qt_item.item_name
	cs.save(ignore_permissions=True)
	return cs.name
