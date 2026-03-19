# Copyright (c) 2026, munyaradzi chirove and contributors
# For license information, please see license.txt

from frappe.model.document import Document

class JobQuote(Document):

	def calculate_table_totals(self, child_table_fieldname, total_amount_field, total_qty_field):
		total_amount = 0
		total_qty = 0
		for row in getattr(self, child_table_fieldname, []):
			# default qty to 1 if empty
			if not row.qty:
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

		# now consolidate all tables into grand totals
		self.total_amount = sum(getattr(self, f"task{i}_total_amount", 0) for i in range(1, 11))
		self.total_quantity = sum(getattr(self, f"task{i}_total_qty", 0) for i in range(1, 11))