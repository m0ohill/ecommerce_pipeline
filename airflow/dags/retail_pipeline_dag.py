
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = "/opt/airflow/project"

with DAG(
    dag_id="retail_etl_pipeline",
    description="Retail CSV ETL to PostgreSQL with data quality checks",
    start_date=datetime(2026, 10, 1),
    schedule=None,
    catchup=False,
    default_args={
        "owner": "data_engineering",
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["retail", "etl", "postgresql"],
) as dag:

    ingest = BashOperator(
        task_id="ingest_csv",
        bash_command=f"cd {PROJECT} && python src/ingest.py",
    )

    transform = BashOperator(
        task_id="transform_data",
        bash_command=f"cd {PROJECT} && python src/transform.py",
    )

    load_postgres = BashOperator(
        task_id="load_postgres",
        bash_command=f"cd {PROJECT} && python src/load_postgres.py",
        env={
            "DATABASE_URL": (
                "postgresql://retail_user:retail_dev_password"
                "@host.docker.internal:5434/retail_db"
            ),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        },
    )

    validate = BashOperator(
        task_id="validate_data",
        bash_command=(
            f"cd {PROJECT} && "
            "python -c \"import os, psycopg; "
            "conn=psycopg.connect(os.environ['DATABASE_URL']); "
            "cur=conn.cursor(); "
            "cur.execute('SELECT COUNT(*) FROM retail_transactions'); "
            "print('PostgreSQL records:', cur.fetchone()[0]); "
            "conn.close()\""
        ),
        env={
            "DATABASE_URL": (
                "postgresql://retail_user:retail_dev_password"
                "@host.docker.internal:5434/retail_db"
            ),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        },
    )

    ingest >> transform >> load_postgres >> validate
