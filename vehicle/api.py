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