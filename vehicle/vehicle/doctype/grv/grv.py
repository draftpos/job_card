# Copyright (c) 2026, munyaradzi chirove and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GRV(Document):
	def befefore_save(sel	f):
		# Ensure that the GRV is linked to a Vehicle Purchase Order
		if not self.job_quote:
			frappe.throw("GRV must be linked to a Vehicle Purchase Order (Job Quote).")		




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