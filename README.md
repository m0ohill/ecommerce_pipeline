# E-commerce Data Engineering Pipeline

**Python · PostgreSQL · SQL · Apache Airflow · Docker**

An end-to-end data engineering portfolio project that ingests, cleans, validates, and stores **1,067,371 historical online retail transaction records**. The project combines Python-based ETL, PostgreSQL bulk loading, SQL analytics, a CSV-based incremental-loading demonstration, and Apache Airflow orchestration.

> **Status:** Working local-development MVP. One Airflow DAG run completed successfully with all four tasks green in **57 seconds**. Production-grade deployment, automated enforcement of all quality rules, and database-native incremental ingestion are future enhancements.

## At a glance

| Metric | Result |
| --- | ---: |
| Source CSV batches | 2 |
| Total processed and loaded records | **1,067,371** |
| 2009–2010 batch | 525,461 |
| 2010–2011 batch | 541,910 |
| PostgreSQL records inserted on unchanged rerun | **0** |
| Records with missing invoice, stock code, or date | **0** |
| Records with incorrect calculated totals | **0** |
| Unexpected negative prices | **0** |
| Negative-price accounting adjustments | **5** |
| Duplicate `(source_file, source_row)` keys | **0** |
| Airflow tasks in successful run | **4 / 4** |
| Recorded Airflow run duration | **57 seconds** |

## Business problem

Retail transaction data often arrives in separate batches and contains returns, cancellations, missing values, and accounting adjustments. Analysts need a repeatable way to convert those files into consistent, queryable data without losing meaningful transactions or inserting the same source rows repeatedly.

This project demonstrates a local pipeline that prepares retail data for downstream sales analysis while retaining the distinctions between sales, returns/cancellations, and adjustments.

## Architecture

```text
                   Historical retail CSV batches
                  (2009–2010 and 2010–2011)
                               |
                               v
                        Python ingestion
                        src/ingest.py
                               |
                               v
                     Python transformation
                      src/transform.py
                        /            \
                       v              v
              Processed CSVs      Quarantine output
                       |
                       v
               PostgreSQL bulk loader
                 src/load_postgres.py
                       |
                       v
               retail_transactions table
                       |
                       v
                SQL analysis & checks
                 sql/data_quality.sql

         Apache Airflow orchestrates four tasks:
        ingest_csv -> transform_data -> load_postgres
                              -> validate_data

  Separate demonstration: src/incremental.py tracks processed
       records in CSV output and a processed-key state file.
```

**Important distinction:** The current Airflow `validate_data` task verifies the PostgreSQL row count. The more extensive checks in `sql/data_quality.sql` have been executed separately; they are **not yet configured to fail the DAG automatically**. The existing incremental loader is CSV/state-file based, not a PostgreSQL incremental writer.

## Tech stack

| Technology | Purpose |
| --- | --- |
| Python | CSV ingestion, profiling, transformation, validation, and incremental demo |
| PostgreSQL 17 | Persistent transaction storage and analytics |
| Psycopg 3 | Python-to-PostgreSQL connection and `COPY` loading |
| SQL | Quality checks and exploratory analytics |
| Apache Airflow 2.10.5 | Workflow orchestration and task monitoring |
| Docker / Docker Compose | Local PostgreSQL and Airflow environments |
| `unittest` | Unit tests for record transformation |
| Git / GitHub | Version control and project presentation |

## Dataset

The project uses two historical retail CSV files:

| Source | Rows |
| --- | ---: |
| `data/raw/batch_001/2009-2010.csv` | 525,461 |
| `data/raw/batch_002/2010-2011.csv` | 541,910 |
| **Total** | **1,067,371** |

The files appear consistent with the **Online Retail II** dataset. Confirm the original download source and its usage terms before adding a formal dataset attribution or redistributing data.

The processed schema contains:

```text
invoice, stock_code, description, quantity, invoice_date,
price, customer_id, country, total_amount, transaction_type
```

`total_amount` is calculated as `quantity * price`. The pipeline categorizes transactions as `sale`, `return_or_cancellation`, or `adjustment`.

## Repository layout

```text
ecommerce_pipeline/
├── airflow/
│   ├── dags/
│   │   └── retail_pipeline_dag.py
│   ├── logs/                     # Generated locally
│   └── plugins/
├── data/
│   ├── raw/
│   │   ├── batch_001/
│   │   └── batch_002/
│   ├── processed/                # Generated CSVs
│   ├── quarantine/               # Generated as needed
│   ├── incremental/              # CSV-based incremental state/output
│   └── incremental_demo/
├── sql/
│   └── data_quality.sql
├── src/
│   ├── ingest.py
│   ├── profile_data.py
│   ├── transform.py
│   ├── validate.py
│   ├── compare_batches.py
│   ├── incremental.py
│   ├── prepare_incremental_demo.py
│   └── load_postgres.py
├── tests/
│   └── test_transform.py
├── docker-compose.yml
└── README.md
```

Some data directories and outputs are generated by the scripts. Check your checkout for the exact files present.

## Implemented features

### 1. Ingestion and profiling

- Reads two historical transaction batches, totaling **1,067,371 rows**.
- Profiles source data to identify missing values, unusual quantities and prices, and potentially duplicate-looking records.
- Preserves repeated-looking transaction lines rather than assuming every match is an error.

### 2. Transformation and validation

- Normalizes column names and parses invoice timestamps.
- Validates required identifiers, quantity values, and numeric prices.
- Calculates transaction totals.
- Classifies sales, returns/cancellations, and adjustments.
- Supports quarantining invalid records with reasons and source context.

In the recorded run, **1,067,371 rows passed the implemented transformation rules** and **0 were quarantined**. Passing these checks does not imply the source data is error-free in every possible business sense.

### 3. PostgreSQL loading

`src/load_postgres.py` bulk-loads transformed CSVs into `retail_transactions` using PostgreSQL `COPY` via Psycopg. The destination table stores source-file and source-row metadata, with a uniqueness constraint on `(source_file, source_row)`.

The initial load inserted:

```text
2009-2010_transformed.csv: 525461 new rows
2010-2011_transformed.csv: 541910 new rows
Total PostgreSQL records: 1067371
```

A second run against **unchanged input files** inserted **0** rows, confirming rerun idempotency under those conditions. Because the key depends on source row position, it is not a robust solution for reordered or modified files.

### 4. CSV-based incremental loading

`src/incremental.py` maintains a destination CSV and a processed-key state file. It uses SHA-256-based record tracking to skip previously seen records in controlled cumulative snapshots.

| Snapshot | Rows available | New rows loaded | Rows skipped | Cumulative stored |
| --- | ---: | ---: | ---: | ---: |
| Day 1 | 10 | 10 | 0 | 10 |
| Day 3 | 35 | 25 | 10 | 35 |
| Day 7 | 150 | 115 | 35 | 150 |

**Limitation:** This is a separate CSV-based demonstration. It has not yet been integrated into PostgreSQL as a production-style incremental upsert pipeline.

### 5. SQL analytics and quality checks

`sql/data_quality.sql` checks missing identifiers/dates, zero quantities, calculated totals, unexpected negative prices, invalid sale quantities, transaction categories, and duplicate source keys.

Recorded transaction-type results:

| Transaction type | Rows | Total amount |
| --- | ---: | ---: |
| `sale` | 1,044,415 | 20,961,906.08 |
| `return_or_cancellation` | 22,950 | -1,527,041.43 |
| `adjustment` | 6 | -147,614.08 |

Five negative-price entries are labeled **“Adjust bad debt”** and classified as adjustments. They are retained rather than incorrectly rejected as invalid sales. There are six adjustment records overall.

An example analysis query:

```sql
SELECT
    country,
    COUNT(*) AS total_transactions,
    ROUND(SUM(total_amount), 2) AS total_revenue
FROM retail_transactions
WHERE transaction_type = 'sale'
GROUP BY country
ORDER BY total_revenue DESC
LIMIT 10;
```

The recorded top market was **United Kingdom**, with **961,218 sale records** and **17,860,289.29** in summed sales amount. The source currency is not asserted here.

### 6. Airflow orchestration

The DAG `retail_etl_pipeline` orchestrates:

```text
ingest_csv -> transform_data -> load_postgres -> validate_data
```

A manual run completed successfully in **57 seconds**, with all four tasks marked successful. The DAG currently uses a manual trigger (`schedule=None`). The final task checks that PostgreSQL can be queried and prints the row count; enforcing the full SQL rules is a planned enhancement.

### 7. Unit testing

Seven transformation unit tests have passed, covering valid records, invalid dates, missing invoice and stock code, fractional quantity, and preservation of negative prices/quantities when appropriate.

## Running locally

> These instructions describe the demonstrated local setup, not a one-command production deployment. You need the dataset files, a working Docker Desktop installation, and Python dependencies.

### Prerequisites

- Python 3
- Docker Desktop with sufficient memory for Airflow
- PostgreSQL container accessible to the host at `localhost:5434`
- The two source CSV files in their expected directories
- Python package `psycopg[binary]`

### 1. Clone the repository

```bash
git clone git@github.com:m0ohill/ecommerce_pipeline.git
cd ecommerce_pipeline
python3 -m pip install 'psycopg[binary]'
```

### 2. Add the source data

```text
data/raw/batch_001/2009-2010.csv
data/raw/batch_002/2010-2011.csv
```

The large CSV files may not be included in the repository. Obtain them from the appropriate source before running the ETL.

### 3. Run the Python pipeline

```bash
python3 src/ingest.py
python3 src/profile_data.py
python3 src/transform.py
```

### 4. Run the PostgreSQL loader

The demonstrated development environment uses a PostgreSQL 17 container named `ecommerce-postgres`, database `retail_db`, and host port `5434`. Configure `DATABASE_URL` for your own environment rather than relying on a hard-coded development password.

```bash
python3 src/load_postgres.py
```

Verify the row count:

```bash
docker exec ecommerce-postgres psql -U retail_user -d retail_db \
  -c 'SELECT COUNT(*) FROM retail_transactions;'
```

### 5. Run the SQL checks

```bash
docker exec -i ecommerce-postgres \
  psql -U retail_user -d retail_db \
  < sql/data_quality.sql
```

These are currently **diagnostic SQL queries**; reviewing their output is still necessary.

### 6. Run the incremental demonstration

```bash
python3 src/prepare_incremental_demo.py
python3 src/incremental.py --demo
```

### 7. Run unit tests

```bash
python3 -m unittest discover -s tests -v
```

### 8. Start Airflow

```bash
docker compose up -d
```

Open the local Airflow UI at `http://localhost:8080`, sign in, and trigger `retail_etl_pipeline`. In the demonstrated setup, Airflow connects to PostgreSQL over the shared Docker network using hostname `ecommerce-postgres` and port `5432` (not the Mac host's port `5434`).

**Networking note:** The existing PostgreSQL container was manually attached to the Compose network during setup. If containers are recreated, that connection may need to be restored or replaced with a persistent Compose network configuration.

**Development-only note:** The current Airflow setup uses SQLite metadata and `SequentialExecutor`. It is suitable for local experimentation, not production. Keep database credentials out of committed source files when preparing a public repository.

## Key engineering decisions and trade-offs

- **Preserve financial meaning:** Negative quantities and negative prices are not always errors; returns and bad-debt adjustments are classified separately from sales.
- **Use bulk loading:** PostgreSQL `COPY` handles the historical dataset efficiently.
- **Prevent simple rerun duplicates:** A source-file/row-position constraint prevents reinserting unchanged batches.
- **Separate experiments:** The CSV incremental demo proves state tracking without claiming database-native incremental ingestion.
- **Make limitations explicit:** The current DAG validates row count; the standalone SQL checks do not yet automatically block a bad load.

## Roadmap

- [x] Ingest and profile two historical CSV batches
- [x] Transform and validate transaction records
- [x] Implement quarantine handling
- [x] Demonstrate CSV-based incremental loading
- [x] Load historical records into PostgreSQL
- [x] Verify duplicate-safe reruns for unchanged CSV files
- [x] Run SQL analytics and data-quality checks
- [x] Orchestrate a successful four-task Airflow DAG
- [ ] Fail the Airflow DAG automatically on data-quality violations
- [ ] Add stable record identity and database-native incremental upserts
- [ ] Persist Docker networking and externalize credentials
- [ ] Add full pipeline integration tests and monitoring
- [ ] Add architecture and Airflow run screenshots to the repository

## Results and learning

This project demonstrates practical experience with **batch ETL design, data profiling, business-rule-aware validation, relational storage, SQL analytics, idempotent reruns, basic incremental state tracking, Docker networking, and Airflow orchestration**. It also illustrates why a working local pipeline is not the same as a production-ready data platform: stable source identities, automated quality gates, credential management, and recovery semantics still matter.

---

*Portfolio project for learning and demonstrating data engineering workflows.*
