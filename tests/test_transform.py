import math
import unittest
from datetime import datetime


def transform_record(row):
    """Validate and transform one retail transaction."""

    invoice = str(row.get("Invoice", "")).strip()
    stock_code = str(row.get("StockCode", "")).strip()
    quantity = float(row.get("Quantity", ""))
    price = float(row.get("Price", ""))

    if not invoice or not stock_code:
        raise ValueError("Invoice and StockCode are required")

    if not math.isfinite(quantity) or not quantity.is_integer():
        raise ValueError("Quantity must be a finite integer")

    if not math.isfinite(price):
        raise ValueError("Price must be finite")

    invoice_date = datetime.strptime(
        row["InvoiceDate"], "%d/%m/%Y %H:%M"
    )

    return {
        "invoice": invoice,
        "stock_code": stock_code,
        "quantity": int(quantity),
        "price": price,
        "invoice_date": invoice_date.isoformat(sep=" "),
        "total_amount": price * quantity,
    }


class TestTransformRecord(unittest.TestCase):

    def setUp(self):
        self.valid_row = {
            "Invoice": "536365",
            "StockCode": "85123A",
            "Quantity": "2",
            "Price": "3.50",
            "InvoiceDate": "01/12/2010 08:26",
        }

    def test_valid_record(self):
        result = transform_record(self.valid_row)
        self.assertEqual(result["invoice"], "536365")
        self.assertEqual(result["quantity"], 2)
        self.assertAlmostEqual(result["total_amount"], 7.00)

    def test_negative_quantity_is_preserved(self):
        row = {**self.valid_row, "Quantity": "-2"}
        result = transform_record(row)
        self.assertEqual(result["quantity"], -2)
        self.assertAlmostEqual(result["total_amount"], -7.00)

    def test_negative_price_is_preserved(self):
        row = {**self.valid_row, "Price": "-5"}
        result = transform_record(row)
        self.assertAlmostEqual(result["price"], -5.00)

    def test_missing_invoice_is_rejected(self):
        row = {**self.valid_row, "Invoice": ""}
        with self.assertRaises(ValueError):
            transform_record(row)

    def test_missing_stock_code_is_rejected(self):
        row = {**self.valid_row, "StockCode": ""}
        with self.assertRaises(ValueError):
            transform_record(row)

    def test_fractional_quantity_is_rejected(self):
        row = {**self.valid_row, "Quantity": "1.5"}
        with self.assertRaises(ValueError):
            transform_record(row)

    def test_invalid_date_is_rejected(self):
        row = {**self.valid_row, "InvoiceDate": "not-a-date"}
        with self.assertRaises(ValueError):
            transform_record(row)


if __name__ == "__main__":
    unittest.main()
