# Copyright (c) 2026, munyaradzi chirove and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _ 


class PartIssue(Document):
	def on_submit(self):
		"""
		Only allow submit if all items in non-empty tables are fully issued.
		If all issued, create Sales Invoice from linked Job Quote and save ID.
		"""
		# 🔹 Check only tables that have items
		for i in range(1, 11):
			table_name = f"table_{i}"
			rows = self.get(table_name) or []
			if not rows:
				continue  # skip empty tables

			for row in rows:
				if not getattr(row, "fully_issued", False):
					frappe.throw(_("Cannot submit: Not all items in table {0} are fully issued!").format(table_name))

		# 🔹 All issued, create Sales Invoice from linked Job Quote
		if not self.job_quote:
			frappe.throw(_("No Job Quote linked to this document!"))

		try:
			quotation = frappe.get_doc("Job Quote", self.job_quote)

			si = frappe.get_doc({
				"doctype": "Sales Invoice",
				"customer": quotation.customer,
				"posting_date": frappe.utils.nowdate(),
				"items": []
			})

			# Copy all items from non-empty tables in Job Quote
			for i in range(1, 11):
				table_name = f"table_{i}"
				rows = quotation.get(table_name) or []
				if not rows:
					continue

				for row in rows:
					si.append("items", {
						"item_code": row.item_code,
						"qty": row.qty,
						"rate": row.rate,
						"amount": row.amount
					})

			si.insert()
			si.submit()

			self.sales_invoice = si.name
			self.status = "Completed"
			self.db_set("sales_invoice", si.name)


			# 🔹 Mark Job Quote as Completed
			quotation.status = "Completed"
			quotation.save()

			frappe.msgprint(_("Sales Invoice {0} created ").format(si.name))

		except Exception as e:
			frappe.throw(_("Failed to create Sales Invoice: {0}").format(e))

			
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