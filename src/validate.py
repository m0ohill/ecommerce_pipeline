
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"


def read_orders(batch_name):
    """Read orders from a batch CSV file."""

    file_path = RAW_DIR / batch_name / "orders.csv"

    with file_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def validate_order(order):
    """Return a list of validation errors for one order."""

    errors = []

    if not order.get("order_id", "").strip():
        errors.append("Missing order_id")

    if not order.get("customer_id", "").strip():
        errors.append("Missing customer_id")

    amount = order.get("amount", "").strip()

    try:
        amount_value = Decimal(amount)

        if not amount_value.is_finite():
            errors.append("Amount must be a finite number")
        elif amount_value < 0:
            errors.append("Amount cannot be negative")

    except InvalidOperation:
        errors.append("Amount is not a valid number")

    return errors


def validate_batch(batch_name):
    """Validate orders and report valid and invalid records."""

    orders = read_orders(batch_name)
    seen_order_ids = set()

    valid_orders = []
    invalid_orders = []

    for order in orders:
        errors = validate_order(order)

        order_id = order.get("order_id", "").strip()

        if order_id:
            if order_id in seen_order_ids:
                errors.append("Duplicate order_id within batch")
            else:
                seen_order_ids.add(order_id)

        if errors:
            invalid_orders.append({
                "record": order,
                "errors": errors
            })
        else:
            valid_orders.append(order)

    print(f"\nValidation results for {batch_name}")
    print("-" * 40)
    print(f"Total records: {len(orders)}")
    print(f"Valid records: {len(valid_orders)}")
    print(f"Invalid records: {len(invalid_orders)}")

    for item in invalid_orders:
        print(f"Invalid record: {item['record']}")
        print(f"Reasons: {item['errors']}")

    return valid_orders, invalid_orders


def main():
    validate_batch("batch_001")
    validate_batch("batch_002")


if __name__ == "__main__":
    main()
