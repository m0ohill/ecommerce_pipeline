
import csv
import os
from pathlib import Path

import psycopg

BASE_DIR = Path(__file__).resolve().parent.parent
FILES = [
    BASE_DIR / "data/processed/2009-2010_transformed.csv",
    BASE_DIR / "data/processed/2010-2011_transformed.csv",
]

COLUMNS = [
    "invoice", "stock_code", "description", "quantity",
    "invoice_date", "price", "customer_id", "country",
    "total_amount", "transaction_type"
]

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://retail_user:retail_dev_password@localhost:5434/retail_db"
)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS retail_transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    invoice TEXT,
    stock_code TEXT,
    description TEXT,
    quantity INTEGER,
    invoice_date TIMESTAMP,
    price NUMERIC(14, 4),
    customer_id TEXT,
    country TEXT,
    total_amount NUMERIC(16, 4),
    transaction_type TEXT,
    source_file TEXT NOT NULL,
    source_row BIGINT NOT NULL,
    UNIQUE (source_file, source_row)
);
"""

def load_file(conn, filepath):
    if not filepath.exists():
        raise FileNotFoundError(filepath)

    print(f"Loading {filepath.name}...")

    with conn.cursor() as cur:
        cur.execute("""
            CREATE TEMP TABLE staging_transactions (
                invoice TEXT,
                stock_code TEXT,
                description TEXT,
                quantity INTEGER,
                invoice_date TIMESTAMP,
                price NUMERIC(14, 4),
                customer_id TEXT,
                country TEXT,
                total_amount NUMERIC(16, 4),
                transaction_type TEXT
            ) ON COMMIT DROP
        """)

        with filepath.open("r", encoding="utf-8-sig", newline="") as f:
            header = f.readline().strip().split(",")
            if header != COLUMNS:
                raise ValueError(f"Unexpected columns: {header}")
            with cur.copy(
                "COPY staging_transactions FROM STDIN WITH (FORMAT CSV)"
            ) as copy:
                for chunk in iter(lambda: f.read(1024 * 1024), ""):
                    copy.write(chunk)

        cur.execute("""
            INSERT INTO retail_transactions (
                invoice, stock_code, description, quantity,
                invoice_date, price, customer_id, country,
                total_amount, transaction_type,
                source_file, source_row
            )
            SELECT
                invoice, stock_code, description, quantity,
                invoice_date, price, customer_id, country,
                total_amount, transaction_type,
                %s,
                ROW_NUMBER() OVER (ORDER BY ctid)
            FROM staging_transactions
            ON CONFLICT (source_file, source_row) DO NOTHING
        """, (filepath.name,))

        print(f"New rows inserted: {cur.rowcount}")




def main():
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE)

        for filepath in FILES:
            load_file(conn, filepath)
            conn.commit()

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM retail_transactions")
            count = cur.fetchone()[0]

        print(f"\nTotal PostgreSQL records: {count:,}")
        print("PostgreSQL loading complete!")


if __name__ == "__main__":
    main()
