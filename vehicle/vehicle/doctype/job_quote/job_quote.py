# Copyright (c) 2026, munyaradzi chirove and contributors
# For license information, please see license.txt
import frappe
from frappe.utils import nowdate, flt
from frappe.model.document import Document

class JobQuote(Document):
	
	def before_submit(self):
		not_fully_issued = []

		for i in range(1, 11):
			table_field = f"table_{i}"

			for row in getattr(self, table_field, []):
				if row.item_code and not getattr(row, "fully_issued", False):
					not_fully_issued.append(f"{row.item_code} (Table {i})")

		# if not_fully_issued:
		# 	frappe.throw(
		# 		"Cannot submit. The following items are not fully issued:<br><br>"
		# 		+ "<br>".join(not_fully_issued)
		# 	)

	def calculate_table_totals(self, child_table_fieldname, total_amount_field, total_qty_field):
		total_amount = 0
		total_qty = 0
		for row in getattr(self, child_table_fieldname, []):
			# default qty to 1 if empty
			if row.qty is None:
				row.qty = 1

			# calculate amount
			row.amount = (row.qty or 0) * (row.rate or 0)

			total_amount += row.amount
			total_qty += row.qty

		# set totals in parent doc
		setattr(self, total_amount_field, total_amount)
		setattr(self, total_qty_field, total_qty)

	def validate(self):
		# first, calculate per-table totals
		for i in range(1, 11):
			table_field = f"table_{i}"
			total_amount_field = f"task{i}_total_amount"
			total_qty_field = f"task{i}_total_qty"
			if hasattr(self, table_field):
				self.calculate_table_totals(table_field, total_amount_field, total_qty_field)

				# 🔹 validation: check each row for fully & partly issued
				for row in getattr(self, table_field, []):
					if getattr(row, "fully_issued", False) and getattr(row, "partly_issued", False):
						frappe.throw(f"Item {row.item_code} in {table_field} cannot be both fully issued and partly issued.")

		# now consolidate all tables into grand totals
		self.total_amount = sum(getattr(self, f"task{i}_total_amount", 0) for i in range(1, 11))
		self.total_quantity = sum(getattr(self, f"task{i}_total_qty", 0) for i in range(1, 11))
		
	def on_submit(self):
			self.create_sales_quotation()

	from frappe.utils import nowdate, flt

	def create_sales_quotation(self):
		try:
			qt = frappe.new_doc("Quotation")
			# qt.company = self.company or frappe.defaults.get_defaults().company
			qt.naming_series = "SAL-QTN-.YYYY.-"
			qt.name = None
			qt.quotation_to = "Customer"
			qt.party_name = self.customer
			qt.transaction_date = nowdate()

			items_map = {}

			for i in range(1, 11):
				table_field = f"table_{i}"
				rows = getattr(self, table_field, [])

				for row in rows:
					if not row.item_code:
						continue

					qty = flt(row.qty) if row.qty is not None else 1
					rate = flt(row.rate)

					key = (row.item_code, rate)

					if key not in items_map:
						items_map[key] = {
							"item_code": row.item_code,
							"qty": 0,
							"rate": rate,
							"description": row.description
						}

					items_map[key]["qty"] += qty

			# 🚨 No items check
			if not items_map:
				frappe.throw("Cannot create Quotation: No items found in tables.")

			# 📦 Append aggregated items
			for item in items_map.values():
				qt.append("items", item)

			qt.set_missing_values()
			qt.calculate_taxes_and_totals()
			qt.insert(ignore_permissions=True)
			qt.submit()

			# 🔗 Link back
			self.db_set("quotation", qt.name)

			frappe.msgprint(f"Quotation <b>{qt.name}</b> created successfully", alert=True)

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Job Quote Conversion Error")
			frappe.throw(f"Error creating quotation: {str(e)}")