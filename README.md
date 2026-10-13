# E-commerce Data Engineering ETL Pipeline

A Python-based data engineering project that processes more than one million online retail transaction records. The project demonstrates data ingestion, profiling, transformation, validation, quarantine handling, and incremental loading. PostgreSQL integration and workflow orchestration are planned next.

## Project Goals

- Build a practical end-to-end ETL pipeline.
- Process raw retail transaction CSV files into a consistent format.
- Profile data and identify quality issues before transformation.
- Validate records and quarantine invalid data with reasons.
- Demonstrate incremental loading without repeatedly loading records already processed.
- Extend the pipeline with PostgreSQL and Apache Airflow.

## Technology Stack

**Implemented**
- Python
- CSV processing
- Logging
- SHA-256 record keys for incremental-load state tracking
- Python unit tests

**Planned**
- PostgreSQL
- SQL-based analysis and validation
- Apache Airflow orchestration
- Expanded integration tests and monitoring

## Dataset Source

The project uses two online retail transaction CSV files:

- `2009-2010.csv`
- `2010-2011.csv`

Based on the filenames and fields, these files appear consistent with the **Online Retail II** dataset, commonly associated with the UCI Machine Learning Repository. Confirm the source you downloaded them from before attributing the dataset to a particular repository. If you obtained it from UCI, cite the [UCI Machine Learning Repository — Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii) here.

| Source file | Records |
|---|---:|
| `2009-2010.csv` | 525,461 |
| `2010-2011.csv` | 541,910 |
| **Total** | **1,067,371** |

The source fields include invoice, stock code, description, quantity, invoice date, price, customer ID, and country.

## Business Case Study

This project simulates the data engineering workflow of an **online retail business** that needs to turn raw transaction files into reliable, analysis-ready data.

The pipeline is designed to help prepare transaction data for questions such as:

- How do sales and transaction volumes change over time?
- Which products generate the most sales?
- How do customer purchasing patterns vary?
- How should returns, cancellations, and adjustments be represented?
- How can downstream analysts query consistent data without repeatedly processing all historical records?

The current focus is on the data engineering foundation: ingestion, profiling, transformation, validation, quarantine handling, and incremental loading. Sales and customer analytics, PostgreSQL storage, and orchestration are future extensions; they should not be considered implemented until those parts are built.

> Dataset note: Place the source files in the expected `data/raw/` directories before running the pipeline. Ensure you have the rights to redistribute the dataset before committing raw data to GitHub.

## Pipeline Overview

```text
Raw CSV batches
      |
      v
Ingestion
      |
      v
Data profiling
      |
      v
Transformation and validation
      |
      +------> Quarantine invalid records
      |
      v
Processed CSV files
      |
      v
Incremental loading and processed-record state
      |
      v
PostgreSQL (planned)
      |
      v
SQL analysis and validation (planned)

Apache Airflow orchestration (planned)
```

## Project Structure

```text
ecommerce-etl-pipeline/
├── data/
│   ├── raw/
│   │   ├── batch_001/
│   │   └── batch_002/
│   ├── processed/
│   ├── quarantine/
│   ├── incremental/
│   └── incremental_demo/
│       ├── source/
│       └── output/
├── src/
│   ├── ingest.py
│   ├── profile_data.py
│   ├── transform.py
│   ├── validate.py
│   ├── compare_batches.py
│   ├── incremental.py
│   └── prepare_incremental_demo.py
├── tests/
│   └── test_transform.py
└── README.md
```

Some folders and files are created when the scripts run. The structure above describes the main project components; your actual repository may differ slightly.

## Implemented Features

### 1. Data ingestion

`src/ingest.py` reads the two raw CSV batches.

- Batch 1: 525,461 records
- Batch 2: 541,910 records
- Total: 1,067,371 records

### 2. Data profiling

`src/profile_data.py` explores the source data before transformation.

Profiling identified missing customer IDs and descriptions, negative quantities, a small number of negative prices associated with bad-debt adjustments, and records that look similar under a candidate duplicate key.

Potential duplicate-looking records are not automatically removed because repeated transaction lines may be legitimate. Negative quantities and prices are also preserved where appropriate rather than being blindly discarded.

### 3. Transformation and validation

`src/transform.py` standardizes and validates the source data.

Current processing includes:

- Standardizing column names
- Parsing invoice dates
- Validating required invoice and stock-code fields
- Checking quantity values and finite numeric prices
- Calculating `total_amount = price * quantity`
- Classifying records as sales, returns/cancellations, or adjustments
- Writing invalid records to quarantine CSV files with reasons and source information

Latest run:

| Metric | Records |
|---|---:|
| Input records | 1,067,371 |
| Valid under current rules | 1,067,371 |
| Quarantined | 0 |

All records passed the current parsing and validation rules. This does not mean every record is guaranteed to satisfy all possible business rules; more comprehensive business-level quality checks can be added later.

### 4. Incremental loading

`src/incremental.py` implements incremental loading using:

- A destination CSV file
- A separate processed-key state file
- SHA-256 hashes to track records already processed
- Logging for new, skipped, and total processed records

Run the full-dataset incremental loader with:

```bash
python src/incremental.py
```

By default, it reads:

- `data/processed/2009-2010_transformed.csv`
- `data/processed/2010-2011_transformed.csv`

It writes to:

- `data/incremental/retail_transactions.csv`
- `data/incremental/processed_keys.csv`

The state file allows the loader to skip records it has already processed when the same input records are encountered again.

**Current limitation:** the record key uses the source row number and row values. This works for the controlled experiment when row order remains stable, but a production implementation should use a stable source identifier or another reliable record identity and should address transaction safety and source changes.

### 5. Incremental-loading demonstration

A small cumulative-snapshot experiment demonstrates how the loader processes newly arrived records without loading previously seen records again.

Prepare the snapshots:

```bash
python src/prepare_incremental_demo.py
```

Run the demonstration:

```bash
python src/incremental.py --demo
```

The demo uses separate files under `data/incremental_demo/` and resets only its own demo output and state before each run. It does not reset the main incremental output.

Successful demonstration results:

| Snapshot | Records in snapshot | Newly loaded | Previously processed and skipped | Total stored |
|---|---:|---:|---:|---:|
| Day 1 | 10 | 10 | 0 | 10 |
| Day 3 | 35 | 25 | 10 | 35 |
| Day 7 | 150 | 115 | 35 | 150 |

This verifies the expected behavior for cumulative snapshots that retain the same record order.

### 6. Unit tests

`tests/test_transform.py` contains seven tests covering:

- Valid record transformation
- Invalid dates
- Missing invoice
- Missing stock code
- Fractional quantity
- Negative price preservation
- Negative quantity preservation

All seven tests passed in the latest recorded test run.

These tests currently exercise a standalone `transform_record(row)` function rather than the entire transformation pipeline. Broader integration tests are a future improvement.

## Setup

### Requirements

- Python 3
- Git
- The two source CSV files

PostgreSQL and Apache Airflow are not required for the currently implemented CSV-based pipeline.

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ecommerce-etl-pipeline
```

Replace the placeholder URL with your repository URL.

### 2. Place the source data

Place the source files at these paths:

```text
data/raw/batch_001/2009-2010.csv
data/raw/batch_002/2010-2011.csv
```

### 3. Run ingestion, profiling, and transformation

```bash
python src/ingest.py
python src/profile_data.py
python src/transform.py
```

Run the scripts in order. Check each script's output before proceeding.

### 4. Run the incremental-loading demonstration

```bash
python src/prepare_incremental_demo.py
python src/incremental.py --demo
```

### 5. Run unit tests

Run from the project root:

```bash
python -m unittest discover -s tests -v
```

## Data and Repository Hygiene

The raw and processed data files can be large. Avoid committing the full retail dataset, generated outputs, or local state files unless you have a specific reason and permission to share them.

A `.gitignore` can exclude local data while keeping empty directory placeholders or documenting expected paths. For example:

```gitignore
# Local datasets and generated outputs
data/raw/*
data/processed/*
data/quarantine/*
data/incremental/*
data/incremental_demo/output/*

# Python cache
__pycache__/
*.py[cod]
```

If you need to preserve empty directory structure, add small `.gitkeep` files where appropriate. Check your repository's existing `.gitignore` before replacing it.

## Planned Improvements

- Load processed transactions into PostgreSQL.
- Design destination tables and verify row counts using SQL.
- Connect incremental loading to PostgreSQL.
- Add more robust record identity and safe recovery behavior.
- Add integration tests for the complete transformation pipeline.
- Orchestrate pipeline stages with Apache Airflow.
- Add concise run summaries and expanded data-quality checks.
- Document SQL examples and add an architecture diagram.

## Current Status

| Component | Status |
|---|---|
| CSV ingestion | Implemented |
| Data profiling | Implemented |
| Transformation and basic validation | Implemented |
| Quarantine handling | Implemented |
| CSV-based incremental loading | Implemented |
| Cumulative-snapshot incremental demo | Tested successfully |
| Initial unit tests | 7 passing |
| PostgreSQL integration | Planned |
| Airflow orchestration | Planned |
| Final documentation and portfolio polish | In progress |

## Next Milestone

The next major milestone is PostgreSQL integration: create the database and target table, load the processed transactions, verify row counts and sample records, and then connect the incremental-loading process to the database.

---

This project is being developed iteratively as a practical data engineering portfolio project. Features marked as planned are not yet implemented.
