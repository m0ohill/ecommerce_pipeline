import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "2009-2010_transformed.csv"
)

DEMO_DIR = PROJECT_DIR / "data" / "incremental_demo" / "source"

BATCHES = {
    "day_1.csv": 10,
    "day_3.csv": 35,
    "day_7.csv": 150,
}


def prepare_batches():
    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    with INPUT_FILE.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        rows = []

        for row in reader:
            rows.append(row)
            if len(rows) == 150:
                break

    if len(rows) < 150:
        raise ValueError("The input file contains fewer than 150 rows.")

    for filename, count in BATCHES.items():
        output_path = DEMO_DIR / filename

        with output_path.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows[:count])

        print(f"{filename}: {count} cumulative records prepared")


if __name__ == "__main__":
    prepare_batches()
