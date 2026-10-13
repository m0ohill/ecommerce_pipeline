
import csv
from pathlib import Path
from collections import Counter

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"


def profile_csv(batch_name, filename):
    file_path = RAW_DIR / batch_name / filename

    with file_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        total_rows = 0
        missing_values = Counter()
        invalid_quantity = 0
        invalid_price = 0
        negative_quantity = 0
        negative_price = 0

        for row in reader:
            total_rows += 1

            for column, value in row.items():
                if value is None or not value.strip():
                    missing_values[column] += 1

            try:
                quantity = int(row["Quantity"])
                if quantity < 0:
                    negative_quantity += 1
            except (ValueError, TypeError):
                invalid_quantity += 1

            try:
                price = float(row["Price"])
                if price < 0:
                    negative_price += 1
            except (ValueError, TypeError):
                invalid_price += 1

    print(f"\nDataset: {filename}")
    print("-" * 45)
    print(f"Total rows: {total_rows}")
    print("Missing values:")
    for column, count in missing_values.items():
        print(f"  {column}: {count}")

    print(f"Invalid quantities: {invalid_quantity}")
    print(f"Invalid prices: {invalid_price}")
    print(f"Negative quantities: {negative_quantity}")
    print(f"Negative prices: {negative_price}")

    
def inspect_negative_prices(batch_name, filename):
    file_path = RAW_DIR / batch_name / filename

    print(f"\nNegative-price records: {filename}")
    print("-" * 70)

    with file_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                price = float(row["Price"])
            except (ValueError, TypeError):
                continue

            if price < 0:
                print(row)


def inspect_negative_quantities(batch_name, filename, limit=10):
    file_path = RAW_DIR / batch_name / filename
    printed = 0

    print(f"\nNegative-quantity records: {filename}")
    print("-" * 70)

    with file_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            try:
                quantity = int(row["Quantity"])
            except (ValueError, TypeError):
                continue

            if quantity < 0:
                print(row)
                printed += 1

                if printed >= limit:
                    break

    print(f"Displayed {printed} records.")


def main():
    profile_csv("batch_001", "2009-2010.csv")
    profile_csv("batch_002", "2010-2011.csv")

    inspect_negative_prices("batch_001", "2009-2010.csv")
    inspect_negative_prices("batch_002", "2010-2011.csv")
    
    inspect_negative_quantities("batch_001", "2009-2010.csv")
    inspect_negative_quantities("batch_002", "2010-2011.csv")


if __name__ == "__main__":
    main()
