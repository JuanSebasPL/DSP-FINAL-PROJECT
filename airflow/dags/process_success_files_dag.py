from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.exceptions import AirflowSkipException

from datetime import datetime, timedelta
import os
import requests
import pandas as pd

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

BASE_DIR = os.path.dirname(__file__) 
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
GOOD_DATA_DIR = os.path.join(DATA_DIR, "good_data")   # folder with ingested files
PROCESSED_LIST = os.path.join(DATA_DIR, "processed_files.txt")

PREDICT_ENDPOINT = "http://127.0.0.1:8000/predict?source=scheduled"   


# -------------------------------------------------------------------
# Utility: load list of already processed files
# -------------------------------------------------------------------
def load_processed_files():
    if not os.path.exists(PROCESSED_LIST):
        return set()
    with open(PROCESSED_LIST, "r") as f:
        return set(line.strip() for line in f.readlines())


# -------------------------------------------------------------------
# Utility: save processed files
# -------------------------------------------------------------------
def save_processed_files(files):
    with open(PROCESSED_LIST, "a") as f:
        for file in files:
            f.write(file + "\n")


# -------------------------------------------------------------------
# Task 1 – Check for NEW DATA
# -------------------------------------------------------------------
def check_for_new_data(**context):
    os.makedirs(GOOD_DATA_DIR, exist_ok=True)

    all_files = [f for f in os.listdir(GOOD_DATA_DIR)
                 if os.path.isfile(os.path.join(GOOD_DATA_DIR, f))]

    processed = load_processed_files()
    new_files = [f for f in all_files if f not in processed]

    if not new_files:
        print("No new ingested files → SKIPPING DAG run.")
        raise AirflowSkipException("No new data found")

    print(f"New files detected: {new_files}")

    # pass list to next task
    context["ti"].xcom_push(key="new_files", value=new_files)


# -------------------------------------------------------------------
# Task 2 – Read new files & make predictions
# -------------------------------------------------------------------
def make_predictions(**context):
    new_files = context["ti"].xcom_pull(key="new_files", task_ids="check_for_new_data")

    for filename in new_files:
        filepath = os.path.join(GOOD_DATA_DIR, filename)
        print(f"Processing {filename}")

        try:
            df = pd.read_csv(filepath)
            payload = df.to_dict(orient="records")

            response = requests.post(
                PREDICT_ENDPOINT,
                json={"data": payload},
                params={"source": "scheduled_job"},
                timeout=15
            )
            response.raise_for_status()

            print(f"✓ Prediction successful for {filename}")
            print("Response:", response.json())

        except Exception as e:
            print(f"ERROR processing {filename}: {e}")

    # mark these files as processed
    save_processed_files(new_files)
    print("Updated processed_files registry.")


# -------------------------------------------------------------------
# DAG DEFINITION
# -------------------------------------------------------------------
with DAG(
    dag_id="process_success_files_dag",
    default_args=default_args,
    description="Scheduled prediction job running every 2 minutes",
    schedule="*/2 * * * *",
    start_date=datetime(2025, 10, 1),
    catchup=False,
) as dag:

    check_task = PythonOperator(
        task_id="check_for_new_data",
        python_callable=check_for_new_data,
        provide_context=True,
    )

    predict_task = PythonOperator(
        task_id="make_predictions",
        python_callable=make_predictions,
        provide_context=True,
    )

    check_task >> predict_task