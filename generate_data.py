
import csv
from pathlib import Path

# Project directory and output location
PROJECT_DIR = Path(__file__).resolve().parent
RAW_DIR = PROJECT_DIR / "data" / "raw" / "batch_001"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Sample customer data
customers = [
    {"customer_id": "C001", "name": "Alice", "country": "Singapore"},
    {"customer_id": "C002", "name": "Ben", "country": "Malaysia"},
    {"customer_id": "C003", "name": "Chloe", "country": "Singapore"},
]

# Sample order data
orders = [
    {
        "order_id": "O1001",
        "customer_id": "C001",
        "order_date": "2026-10-01",
        "amount": 120.00,
        "status": "completed",
    },
    {
        "order_id": "O1002",
        "customer_id": "C002",
        "order_date": "2026-10-02",
        "amount": 80.00,
        "status": "pending",
    },
    {
        "order_id": "O1003",
        "customer_id": "C003",
        "order_date": "2026-10-03",
        "amount": 200.00,
        "status": "completed",
    },
]

# Products purchased
order_items = [
    {
        "order_id": "O1001",
        "product": "Keyboard",
        "quantity": 1,
        "unit_price": 120.00,
    },
    {
        "order_id": "O1002",
        "product": "Mouse",
        "quantity": 2,
        "unit_price": 40.00,
    },
    {
        "order_id": "O1003",
        "product": "Monitor",
        "quantity": 1,
        "unit_price": 200.00,
    },
]


def write_csv(filename, rows):
    """Write a list of dictionaries to a CSV file."""
    if not rows:
        return #return here simply exits the function, doesnt return any value

    output_path = RAW_DIR / filename

    with output_path.open("w", newline="", encoding="utf-8") as file:
        #w: write mode, tells python not to perform its own newline transition, specifies
        # the character encoding 
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        #writes dictionaries in csv format
        writer.writeheader() #write column headers
        writer.writerows(rows) #writes all the data records 

    print(f"Created {output_path}")


def main():
    write_csv("customers.csv", customers)
    write_csv("orders.csv", orders)
    write_csv("order_items.csv", order_items)

    print("Sample data generation complete.")


if __name__ == "__main__":
    main()
