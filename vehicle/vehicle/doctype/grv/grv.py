# Copyright (c) 2026, munyaradzi chirove and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GRV(Document):
	pass

@frappe.whitelist()
def get_vehicle_order(source_name):
	source_doc = frappe.get_doc("Vehicle Purchase Order", source_name)

	target_doc = frappe.new_doc("GRV")

	# --- Copy simple fields ---
	fields_to_copy = [
		"color", "model", "engine_number", "year_model",
		"fuel", "make", "reg_number", "speedometer",
		"body_type", "chasis", "job_quote",
		"customer", "customer_type", "default_price_list",
		"total_amount", "total_quantity"
	]

	for field in fields_to_copy:
		target_doc.set(field, source_doc.get(field))

	# --- Copy task names + totals ---
	for i in range(1, 11):
		target_doc.set(f"task{i}_name", source_doc.get(f"task{i}_name"))
		target_doc.set(f"task{i}_total_amount", source_doc.get(f"task{i}_total_amount"))
		target_doc.set(f"task{i}_total_qty", source_doc.get(f"task{i}_total_qty"))

	# --- Copy child tables ---
	for i in range(1, 11):
		table_name = f"table_{i}"
		for row in source_doc.get(table_name) or []:
			target_doc.append(table_name, {
				"item_code": row.item_code,
				"item_name": row.item_name,
				"description": row.description,
				"qty": row.qty,
				"rate": row.rate,
				"balance_qty":  row.qty,
				"amount": row.amount
			})

	# 🔥 THIS LINE FIXES YOUR ISSUE
	return target_doc.as_dict()



@frappe.whitelist()
def process_grv_item(item_code, qty, purchase_order=None):
    print(f"[GRV] Received item_code: {item_code}, qty: {qty}, purchase_order: {purchase_order}")
    frappe.log_error(f"Received item_code: {item_code}, qty: {qty}, purchase_order: {purchase_order}", "GRV Item Processing")
    return {"success": True, "msg": "Params received bro 🔥"}