import frappe

@frappe.whitelist()
def get_item_prices(item_code):
    if not item_code:
        return {
            "selling_price": 0,
            "buying_price": 0
        }

    selling_price = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "selling": 1},
        "price_list_rate"
    ) or 0

    buying_price = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "buying": 1},
        "price_list_rate"
    ) or 0

    return {
        "selling_price": selling_price,
        "buying_price": buying_price
    }
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, flt

@frappe.whitelist()
def convert_quote_to_wip(job_quote):
    old_doc = frappe.get_doc("Job Quote", job_quote)
    if old_doc.docstatus == 0:
        frappe.throw("Please submit the Job Quote first before converting to WIP.")

    if old_doc.job_wip:
        frappe.throw("Quote already converted to WIP")

    # 🔹 Create new Job Quote (WIP)
    new_doc = frappe.get_doc({
        "doctype": "Job Quote",
        "customer": old_doc.customer,
        "job_quote": old_doc.name, 
        "reg_number": old_doc.reg_number,
        "job_status": "In Progress"
        # copy other fields you want here
    })
    # 🔹 Duplicate child tables
    for i in range(1, 11):
        table_field = f"table_{i}"
        if hasattr(old_doc, table_field):
            for row in getattr(old_doc, table_field):
                new_row = row.as_dict()
                # remove Frappe internals to avoid conflicts
                for key in ("name", "parent", "parentfield", "parenttype", "idx"):
                    new_row.pop(key, None)
                new_doc.append(table_field, new_row)

    new_doc.insert(ignore_permissions=True)

    # 🔹 Link old doc to new WIP
    old_doc.job_wip = new_doc.name
    # old_doc.job_status="In Progress"
    old_doc.save(ignore_permissions=True)

    frappe.msgprint(f"Job Quote converted to WIP successfully: <b>{new_doc.name}</b>")

    return new_doc.name


@frappe.whitelist()
def auto_issue_all(job_quote):
    doc = frappe.get_doc("Job Quote", job_quote)

    updated = False

    for i in range(1, 11):
        table_field = f"table_{i}"

        if not hasattr(doc, table_field):
            continue

        rows = doc.get(table_field) or []

        for row in rows:
            # skip already fully issued
            if row.fully_issued:
                continue

            # 🔥 Auto issue logic
            row.issued_qty = row.qty
            row.fully_issued = 1
            row.partly_issued = 0

            updated = True

    if updated:
        doc.save()
        frappe.db.commit()

    return {"status": "success"}


