import frappe

@frappe.whitelist()
def get_standard_selling_price(item_code):
    """
    Returns the standard selling price of the given item_code.
    """
    if not item_code:
        return 0

    item = frappe.get_doc("Item", item_code)
    
    # 🔹 You can customize this to pull from different price lists if needed
    # Here we assume the field is `standard_rate`
    return item.standard_rate or 0
                