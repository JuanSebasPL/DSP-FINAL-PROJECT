from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os, shutil, random

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR  = os.path.join(DATA_DIR, "raw_data")
GOOD_DATA_DIR = os.path.join(DATA_DIR, "good_data")
BAD_DATA_DIR  = os.path.join(DATA_DIR, "bad_data")

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

def move_one_file():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(GOOD_DATA_DIR, exist_ok=True)
    os.makedirs(BAD_DATA_DIR, exist_ok=True)

    files = [
        f for f in os.listdir(RAW_DATA_DIR)
        if os.path.isfile(os.path.join(RAW_DATA_DIR, f))
    ]
    if not files:
        print("No new files to move.")
        return

  
    filename = random.choice(files)
    src  = os.path.join(RAW_DATA_DIR, filename)

    
    dest = os.path.join(GOOD_DATA_DIR, filename)

    
    shutil.move(src, dest)
    print(f"Moved file: {filename} → {dest}")

with DAG(
    dag_id="process_new_files_dag",
    default_args=default_args,
    description="Move ONE new file from raw_data to good_data/bad_data each run",
    schedule_interval="*/5 * * * *",   # every 5 minutes
    start_date=datetime(2025, 10, 1),
    catchup=False,
    max_active_runs=1,                 # ✅ prevents concurrent bulk moves
) as dag:
    move_new_file = PythonOperator(
        task_id="move_one_file_task",
        python_callable=move_one_file,
    )

    move_new_file
