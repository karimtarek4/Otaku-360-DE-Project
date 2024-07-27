# System imports
import os
import logging
from datetime import datetime

# Airflow imports
from airflow import DAG
from airflow.operators.python import PythonOperator

# Python imports
import pyarrow.csv as pv
import pyarrow.parquet as pq
import requests
import psycopg2
import pandas as pd
import json

from google.cloud import storage
# from airflow.utils.dates import days_ago
# from airflow.operators.bash import BashOperator
# from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator


AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 3,
}


def ingest_cat_facts(api_url):
    """
    Fetches cat facts from the specified API, creates a DataFrame,
    saves it as a CSV file within the Airflow home directory,
    and then reads the saved CSV file to verify its existence (simplified).

    This function assumes the Airflow home directory is accessible
    within the container and has read permissions.
    """

    response = requests.get(api_url)
    response_data = json.loads(response.content)["data"]

    df = pd.DataFrame(response_data)
    df_path = f"{AIRFLOW_HOME}/cat_facts.csv"
    df.to_csv(df_path, index=False)
    print(f"DataFrame created and saved to {df_path}")


def read_csv_and_insert(path):
    """
    Reads the CSV file containing cat facts, extracts facts and lengths,
    and inserts them into the 'cat_facts' table in the PostgreSQL database.
    """

    conn = psycopg2.connect(
        dbname="airflow",
        user="airflow",
        password="airflow",
        host="postgres",  # Assuming postgres container is accessible by name
    )

    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS cat_facts (
                fact VARCHAR(5000) NOT NULL,
                length INTEGER
            );
        """)

        # Read data from CSV and insert into table
        df = pd.read_csv(path)
        for fact in df["fact"]:
            cursor.execute("INSERT INTO cat_facts (fact, length) VALUES (%s, %s)", (fact, len(fact)))
        conn.commit()
        print("Successfully loaded data into the table.")

    except (FileNotFoundError, psycopg2.Error) as e:
        print(f"Error: {e}")

    finally:
        conn.close()


def test_gcs_connection(**kwargs):
    """Tests the connection to Google Cloud Storage."""

    # Create a storage client
    try:
        client = storage.Client()
        print("Successfully connected to Google Cloud Storage!")
    except Exception as e:
        print(f"Error connecting to GCS: {e}")
        raise

# DAG declaration
with DAG(
    dag_id="cat_facts_ingestion_dag",
    start_date=datetime(2019, 1, 1),
    schedule_interval="@daily",
    default_args=default_args,
    catchup=True,
    max_active_runs=1,
    tags=['dtc-de'],
) as dag:

    ingest_cat_facts_task = PythonOperator(
        task_id="ingest_cat_facts_task",
        python_callable=ingest_cat_facts,
        op_kwargs={"api_url": "https://catfact.ninja/facts"},
    )

    read_csv_and_insert_db_task = PythonOperator(
        task_id="read_csv_and_insert_db_task",
        python_callable=read_csv_and_insert,
        op_kwargs={"path": f"{AIRFLOW_HOME}/cat_facts.csv"},
    )

     # Define a task to test the connection
    test_gcs_connection_task = PythonOperator(
        task_id="test_gcs_connection",
        python_callable=test_gcs_connection,
        provide_context=True,
    )

    # Task dependencies
    ingest_cat_facts_task >> read_csv_and_insert_db_task >> test_gcs_connection_task