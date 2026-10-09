
import csv
from pathlib import Path

# Locate the project and incoming data
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"


def read_orders(batch_name):
    """Read the orders from a batch."""

    file_path = RAW_DIR / batch_name / "orders.csv"

    with file_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def compare_batches():
    """Identify new, updated, and unchanged orders."""

    old_orders = read_orders("batch_001")
    new_orders = read_orders("batch_002")

    # Use order_id as the unique identifier for each order.
    old_orders_by_id = {
        order["order_id"]: order #"order_id" is the key 
        for order in old_orders
    }

    #code produces something equivalent to
#     old_orders_by_id = {
#     "O1001": {"order_id": "O1001", "status": "completed"},
#     "O1002": {"order_id": "O1002", "status": "pending"},
#     "O1003": {"order_id": "O1003", "status": "completed"}
# }, 

    for new_order in new_orders:
        order_id = new_order["order_id"]
        old_order = old_orders_by_id.get(order_id)

        if old_order is None:
            print(f"NEW ORDER: {order_id}")

        elif old_order != new_order:
            print(f"UPDATED ORDER: {order_id}")
            print(f"  Before: {old_order}")
            print(f"  After:  {new_order}")

        else:
            print(f"UNCHANGED / DUPLICATE ORDER: {order_id}")


def main():
    compare_batches()


if __name__ == "__main__":
    main()
