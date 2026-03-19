# Copyright (c) 2026, munyaradzi chirove and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class VehiclePurchaseOrder(Document):
    pass


@frappe.whitelist()
def get_job_quote(source_name):
    source_doc = frappe.get_doc("Job Quote", source_name)

    target_doc = frappe.new_doc("Vehicle Purchase Order")

    # --- Copy simple fields ---
    fields_to_copy = [
        "color", "model", "engine_number", "year_model",
        "fuel", "make", "reg_number", "speedometer",
        "body_type", "chasis",
        "first_name", "surname", "customer_type", "default_price_list",
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
        for row in source_doc.get(table_name):
            target_doc.append(table_name, {
                "item_code": row.item_code,
                "item_name": row.item_name,
                "description": row.description,
                "qty": row.qty,
                "rate": row.rate,
                "amount": row.amount
            })

    return target_doc