from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from datetime import datetime, timedelta
import os
import shutil
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
NEW_DIR = os.path.join(DATA_DIR, "new")
SUCCESS_DIR = os.path.join(DATA_DIR, "success")
SUCCESS_PROCESSED_DIR = os.path.join(DATA_DIR, "success_processed")
PREDICT_ENDPOINT = "http://api:8000/predict"

#Read all the files in sucess folder and send the information to the API
def process_success_files():
    os.makedirs(SUCCESS_DIR, exist_ok=True)
    os.makedirs(SUCCESS_PROCESSED_DIR, exist_ok=True)
    files = [f for f in os.listdir(SUCCESS_DIR) if os.path.isfile(os.path.join(SUCCESS_DIR, f))]

    if not files:
        print("No files found in 'success/' directory.")
        return

    for filename in files:
        filepath = os.path.join(SUCCESS_DIR, filename)
        print(f"Processing file: {filename}")

        try:
            df = pd.read_csv(filepath)
            payload = df.to_dict(orient="records")
            response = requests.post(PREDICT_ENDPOINT, json={"data": payload})
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Successfully sent {filename} to {PREDICT_ENDPOINT}")
            print(f"🔍 API Response: {result}")

            dest = os.path.join(SUCCESS_PROCESSED_DIR, filename)
            shutil.move(filepath, dest)
            print(f"Moved file: {filename} → success_processed/")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")


with DAG(
    dag_id="process_success_files_dag",
    default_args=default_args,
    description="Read all success files, send to API, then move to success_processed",
    schedule="*/5 * * * *", 
    start_date=datetime(2025, 10, 1),
    catchup=False,
) as dag:
    process_task = PythonOperator(
        task_id="process_success_files",
        python_callable=process_success_files,
    )

    process_task
