
import csv
import logging
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
QUARANTINE_DIR = PROJECT_DIR / "data" / "quarantine"

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

COLUMN_MAPPING = {
    "Invoice": "invoice",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "price",
    "Customer ID": "customer_id",
    "Country": "country",
}

OUTPUT_COLUMNS = [
    "invoice",
    "stock_code",
    "description",
    "quantity",
    "invoice_date",
    "price",
    "customer_id",
    "country",
    "total_amount",
    "transaction_type",
]

RAW_COLUMNS = list(COLUMN_MAPPING.keys())


def transform_record(row):
    """Transform one retail transaction and return errors."""

    errors = []

    # Standardise column names and trim whitespace.
    record = {
        COLUMN_MAPPING[column]: (row.get(column) or "").strip()
        for column in RAW_COLUMNS
    }

    # Required identifiers.
    if not record["invoice"]:
        errors.append("Missing invoice")

    if not record["stock_code"]:
        errors.append("Missing stock_code")

    # Validate quantity.
    try:
        quantity_decimal = Decimal(record["quantity"])

        if not quantity_decimal.is_finite():
            errors.append("Quantity must be a finite number")
        elif quantity_decimal != quantity_decimal.to_integral_value():
            errors.append("Quantity must be a whole number")
        else:
            quantity = int(quantity_decimal)

    except (InvalidOperation, ValueError):
        errors.append("Quantity is not a valid number")

    # Validate price.
    try:
        price = Decimal(record["price"])

        if not price.is_finite():
            errors.append("Price must be a finite number")

    except (InvalidOperation, ValueError):
        errors.append("Price is not a valid number")

    # Validate transaction date.
    try:
        invoice_date = datetime.strptime(
            record["invoice_date"], "%d/%m/%Y %H:%M"
        )
    except ValueError:
        errors.append("InvoiceDate is missing or has an invalid format")

    # Do not process records that cannot be transformed safely.
    if errors:
        return None, errors

    record["quantity"] = quantity
    record["price"] = str(price)
    record["invoice_date"] = invoice_date.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    record["total_amount"] = str(price * quantity)

    # Missing customer IDs and descriptions are retained.
    # Negative quantities may represent legitimate returns.
    # Negative prices may represent legitimate adjustments.
    if (
        record["stock_code"].upper() == "B"
        or record["description"].lower() == "adjust bad debt"
    ):
        transaction_type = "adjustment"
    elif quantity < 0:
        transaction_type = "return_or_cancellation"
    else:
        transaction_type = "sale"

    record["transaction_type"] = transaction_type

    return record, []


def transform_file(batch_name, filename):
    """Transform a batch, quarantine invalid rows and report metrics."""

    source_path = RAW_DIR / batch_name / filename
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PROCESSED_DIR / filename.replace(
        ".csv", "_transformed.csv"
    )
    quarantine_path = QUARANTINE_DIR / filename.replace(
        ".csv", "_quarantine.csv"
    )

    total_count = 0
    valid_count = 0
    invalid_count = 0

    quarantine_columns = [
        "source_batch",
        "source_file",
        "source_row",
        "quarantine_reason",
        *RAW_COLUMNS,
    ]

    with (
        source_path.open(
            "r", newline="", encoding="utf-8-sig"
        ) as source_file,
        output_path.open(
            "w", newline="", encoding="utf-8"
        ) as output_file,
        quarantine_path.open(
            "w", newline="", encoding="utf-8"
        ) as quarantine_file,
    ):
        reader = csv.DictReader(source_file)

        writer = csv.DictWriter(
            output_file,
            fieldnames=OUTPUT_COLUMNS
        )
        writer.writeheader()

        quarantine_writer = csv.DictWriter(
            quarantine_file,
            fieldnames=quarantine_columns
        )
        quarantine_writer.writeheader()

        for row_number, row in enumerate(reader, start=2):
            total_count += 1

            try:
                transformed_record, errors = transform_record(row)
            except Exception:
                # Unexpected errors are quarantined rather than silently lost.
                transformed_record = None
                errors = ["Unexpected transformation error"]

                logger.exception(
                    "Unexpected error in %s, row %s",
                    filename,
                    row_number
                )

            if errors:
                invalid_count += 1

                quarantine_record = {
                    "source_batch": batch_name,
                    "source_file": filename,
                    "source_row": row_number,
                    "quarantine_reason": "; ".join(errors),
                }

                for column in RAW_COLUMNS:
                    quarantine_record[column] = row.get(column, "")

                quarantine_writer.writerow(quarantine_record)

            else:
                writer.writerow(transformed_record)
                valid_count += 1

    pass_rate = (
        valid_count / total_count * 100
        if total_count else 0
    )
    quarantine_rate = (
        invalid_count / total_count * 100
        if total_count else 0
    )

    logger.info("Results for %s", filename)
    logger.info("Total records: %s", total_count)
    logger.info("Valid records: %s", valid_count)
    logger.info("Quarantined records: %s", invalid_count)
    logger.info("Validation pass rate: %.2f%%", pass_rate)
    logger.info("Quarantine rate: %.2f%%", quarantine_rate)
    logger.info("Processed data: %s", output_path)
    logger.info("Quarantine data: %s", quarantine_path)

    # Every source record must be accounted for.
    assert total_count == valid_count + invalid_count

    return {
        "batch": batch_name,
        "total": total_count,
        "valid": valid_count,
        "quarantined": invalid_count,
        "pass_rate": pass_rate,
        "quarantine_rate": quarantine_rate,
    }


def main():
    results = [
        transform_file("batch_001", "2009-2010.csv"),
        transform_file("batch_002", "2010-2011.csv"),
    ]

    total = sum(result["total"] for result in results)
    valid = sum(result["valid"] for result in results)
    quarantined = sum(
        result["quarantined"] for result in results
    )

    overall_pass_rate = valid / total * 100 if total else 0
    overall_quarantine_rate = (
        quarantined / total * 100 if total else 0
    )

    logger.info("=" * 45)
    logger.info("OVERALL PIPELINE RESULTS")
    logger.info("Total records: %s", total)
    logger.info("Valid records: %s", valid)
    logger.info("Quarantined records: %s", quarantined)
    logger.info(
        "Overall validation pass rate: %.2f%%",
        overall_pass_rate
    )
    logger.info(
        "Overall quarantine rate: %.2f%%",
        overall_quarantine_rate
    )


if __name__ == "__main__":
    main()
