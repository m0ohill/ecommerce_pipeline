
import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"


def read_csv(file_path):
    """Read a CSV file and return its records as dictionaries."""

    with file_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    return rows


def inspect_batch(batch_name, filename):
    """Inspect one batch of retail transaction data."""

    file_path = RAW_DIR / batch_name / filename

    rows = read_csv(file_path)

    print(f"\nInspecting {filename}")
    print("-" * 50)
    print(f"Total records: {len(rows)}")

    if rows:
        print(f"Columns: {list(rows[0].keys())}")
        print("First record:")
        print(rows[0])


def main():
    inspect_batch("batch_001", "2009-2010.csv")
    inspect_batch("batch_002", "2010-2011.csv")


if __name__ == "__main__":
    main()
