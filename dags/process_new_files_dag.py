from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import shutil

BASE_DIR = os.path.dirname(__file__) 
PROJECT_ROOT = os.path.dirname(BASE_DIR) 
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
NEW_DIR = os.path.join(DATA_DIR, "new")
SUCCESS_DIR = os.path.join(DATA_DIR, "success")
PROBLEMS_DIR = os.path.join(DATA_DIR, "problems")

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

#Move files, if the folders do not exists it creates them
def move_files():
    os.makedirs(NEW_DIR, exist_ok=True)
    os.makedirs(SUCCESS_DIR, exist_ok=True)
    os.makedirs(PROBLEMS_DIR, exist_ok=True)
    files = [f for f in os.listdir(NEW_DIR) if os.path.isfile(os.path.join(NEW_DIR, f))]

    if not files:
        print("No new files to move.")
        return

    for filename in files:
        src = os.path.join(NEW_DIR, filename)
        dest = os.path.join(SUCCESS_DIR, filename)
        shutil.move(src, dest)
        print(f"Moved file: {filename} → {SUCCESS_DIR}")

    print(f"All {len(files)} files moved successfully.")


with DAG(
    dag_id="process_new_files_dag",
    default_args=default_args,
    description="Move files from new folder to success/problems",
    schedule="*/5 * * * *", 
    start_date=datetime(2025, 10, 1),
    catchup=False,
) as dag:
    move_new_files = PythonOperator(
        task_id="move_files_task",
        python_callable=move_files,
    )
    move_new_files
