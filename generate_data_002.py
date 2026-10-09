
import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw" / "batch_002"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# A new customer arrives
customers = [
    {
        "customer_id": "C004",
        "name": "Daniel",
        "country": "Singapore",
    }
]

# New order, updated order, and duplicate order
orders = [
    {
        "order_id": "O1004",
        "customer_id": "C004",
        "order_date": "2026-10-04",
        "amount": 150.00,
        "status": "completed",
    },
    {
        "order_id": "O1002",
        "customer_id": "C002",
        "order_date": "2026-10-02",
        "amount": 80.00,
        "status": "completed",
    },
    {
        "order_id": "O1001",
        "customer_id": "C001",
        "order_date": "2026-10-01",
        "amount": 120.00,
        "status": "completed",
    },
]

order_items = [
    {
        "order_id": "O1004",
        "product": "Headphones",
        "quantity": 1,
        "unit_price": 150.00,
    }
]


def write_csv(filename, rows):
    if not rows:
        return

    output_path = RAW_DIR / filename

    with output_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {output_path}")


def main():
    write_csv("customers.csv", customers)
    write_csv("orders.csv", orders)
    write_csv("order_items.csv", order_items)

    print("Batch 002 generation complete.")


if __name__ == "__main__":
    main()
