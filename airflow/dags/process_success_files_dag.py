from airflow import DAG
from airflow.operators.python import PythonOperator
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
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")                      
GOOD_DATA_DIR = os.path.join(DATA_DIR, "good_data")        
SUCCESS_PROCESSED_DIR = os.path.join(DATA_DIR, "good_data_processed")  
PREDICT_ENDPOINT = "http://127.0.0.1:8000/predict?source=scheduled"                

#Read all the files in good_data folder and send the information to the API
def process_success_files():
    os.makedirs(GOOD_DATA_DIR, exist_ok=True)
    os.makedirs(SUCCESS_PROCESSED_DIR, exist_ok=True)
    files = [f for f in os.listdir(GOOD_DATA_DIR) if os.path.isfile(os.path.join(GOOD_DATA_DIR, f))]

    if not files:
        print("No files found in 'good_data/' directory.")         
        return

    for filename in files:
        filepath = os.path.join(GOOD_DATA_DIR, filename)
        print(f"Processing file: {filename}")

        try:
            df = pd.read_csv(filepath)
            payload = df.to_dict(orient="records")
            response = requests.post(PREDICT_ENDPOINT, json={"data": payload})
            response.raise_for_status()
            result = response.json()
            
            print(f"Successfully sent {filename} to {PREDICT_ENDPOINT}")
            print(f"API Response: {result}")

            dest = os.path.join(SUCCESS_PROCESSED_DIR, filename)
            shutil.move(filepath, dest)
            print(f"Moved file: {filename} → good_data_processed/")  

        except Exception as e:
            print(f" Error processing {filename}: {e}")


with DAG(
    dag_id="process_success_files_dag",
    default_args=default_args,
    description="Read all good_data files, send to API, then move to good_data_processed",  
    schedule="*/5 * * * *", 
    start_date=datetime(2025, 10, 1),
    catchup=False,
) as dag:
    process_task = PythonOperator(
        task_id="process_success_files",
        python_callable=process_success_files,
    )

    process_task