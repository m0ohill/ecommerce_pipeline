import csv
import hashlib
import logging
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
INCREMENTAL_DIR = PROJECT_DIR / "data" / "incremental"

INPUT_FILES = [
    "2009-2010_transformed.csv",
    "2010-2011_transformed.csv",
]

OUTPUT_FILE = INCREMENTAL_DIR / "retail_transactions.csv"
STATE_FILE = INCREMENTAL_DIR / "processed_keys.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

logger = logging.getLogger(__name__)


def create_record_key(source_file, row_number, row):
    """Identify a source record without deduplicating identical transactions."""
    record = "|".join(
        [
            source_file,
            str(row_number),
            *(row.get(column, "") or "" for column in sorted(row)),
        ]
    )

    return hashlib.sha256(record.encode("utf-8")).hexdigest()


def run_incremental_load():
    INCREMENTAL_DIR.mkdir(parents=True, exist_ok=True)

    # Refuse to start if only one of the output/state files exists.
    if OUTPUT_FILE.exists() != STATE_FILE.exists():
        raise RuntimeError(
            "Output and state files are inconsistent. "
            "Back them up and reset both before rerunning."
        )

    seen_keys = set()

    if STATE_FILE.exists():
        with STATE_FILE.open(
            "r", newline="", encoding="utf-8"
        ) as state_file:
            seen_keys = {
                row["record_key"]
                for row in csv.DictReader(state_file)
            }

    initial_count = len(seen_keys)
    output_exists = OUTPUT_FILE.exists()
    state_exists = STATE_FILE.exists()

    new_count = 0
    skipped_count = 0

    with (
        OUTPUT_FILE.open("a", newline="", encoding="utf-8") as output_file,
        STATE_FILE.open("a", newline="", encoding="utf-8") as state_file,
    ):
        output_writer = None
        state_writer = csv.DictWriter(
            state_file,
            fieldnames=["record_key"],
        )

        if not state_exists:
            state_writer.writeheader()

        for filename in INPUT_FILES:
            input_path = PROCESSED_DIR / filename

            if not input_path.exists():
                raise FileNotFoundError(input_path)

            with input_path.open(
                "r", newline="", encoding="utf-8-sig"
            ) as input_file:
                reader = csv.DictReader(input_file)

                if not reader.fieldnames:
                    continue

                if output_writer is None:
                    output_writer = csv.DictWriter(
                        output_file,
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
    logger.info("Output file: %s", OUTPUT_FILE)
    logger.info("State file: %s", STATE_FILE)


if __name__ == "__main__":
    run_incremental_load()
