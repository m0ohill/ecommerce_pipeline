import csv
import hashlib
import logging
import argparse
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
INCREMENTAL_DIR = PROJECT_DIR / "data" / "incremental"

DEMO_SOURCE_DIR = PROJECT_DIR / "data" / "incremental_demo" / "source"
DEMO_OUTPUT_DIR = PROJECT_DIR / "data" / "incremental_demo" / "output"

INPUT_FILES = [
    "2009-2010_transformed.csv",
    "2010-2011_transformed.csv",
]

DEMO_INPUT_FILES = [
    "day_1.csv",
    "day_3.csv",
    "day_7.csv",
]

OUTPUT_FILE = INCREMENTAL_DIR / "retail_transactions.csv"
STATE_FILE = INCREMENTAL_DIR / "processed_keys.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


def create_record_key(source_file, row_number, row):
    """Identify the same record consistently across cumulative snapshots."""
    record = "|".join(
        [
            str(row_number),
            *(row.get(column, "") or "" for column in sorted(row)),
        ]
    )

    return hashlib.sha256(record.encode("utf-8")).hexdigest()


def run_incremental_load(
    input_dir=PROCESSED_DIR,
    input_files=INPUT_FILES,
    output_file=OUTPUT_FILE,
    state_file=STATE_FILE,
    reset=False,
):
    input_dir = Path(input_dir)
    output_file = Path(output_file)
    state_file = Path(state_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    # Reset is intended for a controlled demo or deliberate full reload.
    if reset:
        for path in (output_file, state_file):
            if path.exists():
                path.unlink()

    # Refuse to start if only one of the output/state files exists.
    if output_file.exists() != state_file.exists():
        raise RuntimeError(
            "Output and state files are inconsistent. "
            "Back them up and reset both before rerunning."
        )

    seen_keys = set()

    if state_file.exists():
        with state_file.open(
            "r", newline="", encoding="utf-8"
        ) as state:
            seen_keys = {
                row["record_key"]
                for row in csv.DictReader(state)
            }

    initial_count = len(seen_keys)
    output_exists = output_file.exists()
    state_exists = state_file.exists()

    new_count = 0
    skipped_count = 0

    with (
        output_file.open("a", newline="", encoding="utf-8") as output,
        state_file.open("a", newline="", encoding="utf-8") as state,
    ):
        output_writer = None
        state_writer = csv.DictWriter(
            state,
            fieldnames=["record_key"],
        )

        if not state_exists:
            state_writer.writeheader()

        for filename in input_files:
            input_path = input_dir / filename

            if not input_path.exists():
                raise FileNotFoundError(input_path)

            with input_path.open(
                "r", newline="", encoding="utf-8-sig"
            ) as source:
                reader = csv.DictReader(source)

                if not reader.fieldnames:
                    continue

                if output_writer is None:
                    output_writer = csv.DictWriter(
                        output,
                        fieldnames=reader.fieldnames,
                    )

                    if not output_exists:
                        output_writer.writeheader()
                        output_exists = True

                for row_number, row in enumerate(reader, start=2):
                    record_key = create_record_key(
                        filename,
                        row_number,
                        row,
                    )

                    if record_key in seen_keys:
                        skipped_count += 1
                        continue

                    output_writer.writerow(row)
                    state_writer.writerow(
                        {"record_key": record_key}
                    )

                    seen_keys.add(record_key)
                    new_count += 1

    logger.info("Incremental load completed")
    logger.info("Previously processed keys: %s", initial_count)
    logger.info("New records loaded: %s", new_count)
    logger.info("Records skipped on rerun: %s", skipped_count)
    logger.info("Total processed keys: %s", len(seen_keys))
    logger.info("Output file: %s", output_file)
    logger.info("State file: %s", state_file)


def run_demo():
    """Run the same incremental loader against the three cumulative snapshots."""
    for path in (DEMO_OUTPUT_DIR / "retail_transactions.csv",
                 DEMO_OUTPUT_DIR / "processed_keys.csv"):
        if path.exists():
            path.unlink()

    for label, filename in [
        ("Day 1", "day_1.csv"),
        ("Day 3", "day_3.csv"),
        ("Day 7", "day_7.csv"),
    ]:
        logger.info("===== %s =====", label)

        run_incremental_load(
            input_dir=DEMO_SOURCE_DIR,
            input_files=[filename],
            output_file=DEMO_OUTPUT_DIR / "retail_transactions.csv",
            state_file=DEMO_OUTPUT_DIR / "processed_keys.csv",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the incremental-loading demonstration on small snapshots.",
    )
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        run_incremental_load()
