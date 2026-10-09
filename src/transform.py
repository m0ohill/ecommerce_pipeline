
import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"


def read_orders(batch_name):
    """Read orders from a batch CSV file."""

    file_path = RAW_DIR / batch_name / "orders.csv"

    with file_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def merge_batches():
    """Merge batches into one dataset, using order_id as the key."""

    batch_001_orders = read_orders("batch_001")
    batch_002_orders = read_orders("batch_002")

    # Start with the existing orders.
    orders_by_id = {
        order["order_id"]: order
        for order in batch_001_orders
    }

    # Insert new orders or replace existing orders with incoming versions.
    for order in batch_002_orders:
        orders_by_id[order["order_id"]] = order

    # Convert the dictionary values back into a list.
    processed_orders = list(orders_by_id.values())

    return processed_orders


def save_orders(orders):
    """Save the processed orders to a CSV file."""

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DIR / "orders.csv"

    if not orders:
        print("No orders to save.")
        return

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=orders[0].keys())
        writer.writeheader()
        writer.writerows(orders)

    print(f"Saved {len(orders)} orders to {output_path}")


def main():
    processed_orders = merge_batches()
    save_orders(processed_orders)


if __name__ == "__main__":
    main()
