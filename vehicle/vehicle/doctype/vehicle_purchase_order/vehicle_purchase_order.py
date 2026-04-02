# Copyright (c) 2026, munyaradzi chirove and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


# vehicle_purchase_order.py
import frappe
from frappe.model.document import Document
from frappe import _

class VehiclePurchaseOrder(Document):

	def on_submit(self):
		try:
			# --- create new built-in Purchase Order ---
			po = frappe.new_doc("Purchase Order")
			po.supplier = self.supplier
			po.transaction_date = self.creation
			po.schedule_date = self.creation
			po.set("items", [])

			# --- loop all 10 tables and append items ---
			for i in range(1, 11):
				table_name = f"table_{i}"
				for row in getattr(self, table_name, []):
					po.append("items", {
						"item_code": row.item_code,
						"qty": row.qty,
						"rate": row.rate,
						"description": row.description
					})

			# --- insert + submit PO ---
			po.insert()
			po.submit()

			# --- store the created PO ID in Vehicle Purchase Order ---
			# self.purchase_order = po.name
			self.db_set("purchase_order", po.name)
			print(f"--------------calm {po.name}---------")
			# self.db_update() 

			frappe.msgprint(f"Purchase Order {po.name} created successfully!")

		except Exception as e:
			# --- if PO creation fails, Vehicle PO submit fails too ---
			frappe.throw(_("Failed to create Purchase Order: {0}").format(e))

@frappe.whitelist()
def get_job_quote(source_name):
	source_doc = frappe.get_doc("Job Quote", source_name)

	target_doc = frappe.new_doc("Vehicle Purchase Order")

	# --- Copy simple fields ---
	fields_to_copy = [
		"color", "model", "engine_number", "year_model",
		"fuel", "make", "reg_number", "speedometer",
		"body_type", "chasis",
		"customer", "customer_type",
		"total_amount", "total_quantity",
		"total_buying_amount"
		
	]

	for field in fields_to_copy:
		target_doc.set(field, source_doc.get(field))

	# --- Copy task names + totals ---
	for i in range(1, 11):
		target_doc.set(f"task{i}_name", source_doc.get(f"task{i}_name"))
		target_doc.set(f"task{i}_total_amount", source_doc.get(f"task{i}_total_amount"))
		target_doc.set(f"task{i}_total_qty", source_doc.get(f"task{i}_total_qty"))
		target_doc.set(f"task{i}_total_buying_amount", source_doc.get(f"task{i}_total_buying_amount"))

	# --- Copy child tables ---
	for i in range(1, 11):
		table_name = f"table_{i}"
		for row in source_doc.get(table_name):
			target_doc.append(table_name, {
				"item_code": row.item_code,
				"item_name": row.item_name,
				"description": row.description,
				"qty": row.qty,
				"rate": row.rate,
				"amount": row.amount,
				"buying_price": row.buying_price,
				"buying_amount":row.buying_amount,
				"margin": row.margin
			})

	return target_doc