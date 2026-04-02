# Copyright (c) 2026, munyaradzi chirove and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class GRV(Document):
	def before_save(self):
		CHILD_TABLES = [
			"table_1","table_2","table_3","table_4","table_5",
			"table_6","table_7","table_8","table_9","table_10"
		]

		has_balance = False
		found_any = False

		# 🔹 Loop all child tables
		for table in CHILD_TABLES:
			rows = self.get(table) or []

			if rows:
				found_any = True

			for r in rows:
				if (r.get("balance_qty") or 0) > 0:
					has_balance = True
					break

			if has_balance:
				break

		# 🔹 Only update if there are rows
		if found_any:
			self.status = "Partial Received" if has_balance else "Total Received"

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
		"total_amount", "total_quantity","supplier"
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



import frappe
from frappe.utils import nowdate

@frappe.whitelist()
def process_grv_item(item_code, qty, purchase_order=None):
	"""
	Create a Purchase Receipt for the given item and qty from the purchase order.
	"""
	print(f"[GRV] Received item_code: {item_code}, qty: {qty}, purchase_order: {purchase_order}")

	if not purchase_order:
		frappe.throw("Purchase Order not provided!")

	# Get the Vehicle Purchase Order doc
	po = frappe.get_doc("Vehicle Purchase Order", purchase_order)

	# Create Purchase Receipt linked to this PO
	pr = frappe.new_doc("Purchase Receipt")
	pr.purchase_order = po.name
	pr.supplier = po.supplier   # ✅ supplier comes from PO
	pr.posting_date = nowdate()

	# Add item
	pr.append("items", {
		"item_code": item_code,
		"qty": qty,
		"rate": 0,   # or pull from PO item rate if you want
		"amount": 0
	})

	pr.insert()
	pr.submit()

	frappe.msgprint(f"Purchase Receipt {pr.name} created for {item_code}, qty: {qty} ✅")

	return {"success": True, "purchase_receipt": pr.name}




# 🔹 Single function to recalc balances and status
def run_recalc(doc, method=None):
	
	child_tables = [
		"table_1","table_2","table_3","table_4","table_5",
		"table_6","table_7","table_8","table_9","table_10"
	]
	print("---------------------------calculating")

	has_balance = False

	for table_field in child_tables:
		rows = getattr(doc, table_field, []) or []
		for row in rows:
			ordered = flt(row.qty or 0)
			received = flt(row.received_qty or 0)
			row.balance_qty = max(ordered - received, 0)

			if row.balance_qty > 0:
				has_balance = True

	doc.status = "Partial Received" if has_balance else "Total Received"

	# optionally return the job id for tracking
	return {"job_id": doc.name, "status": doc.status}