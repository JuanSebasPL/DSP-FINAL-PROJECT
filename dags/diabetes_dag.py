from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from datetime import datetime

def fetch_data_from_postgres():
    hook = PostgresHook(postgres_conn_id='postgres_conn')
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM diabetes_data;")
    result = cursor.fetchone()
    print(f"Total rows in diabetes_data table: {result[0]}")
    cursor.close()
    conn.close()

default_args = {
    'owner': 'sameer',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='diabetes_data_check',
    default_args=default_args,
    schedule_interval=None,  # Run manually
    catchup=False,
    tags=['postgres', 'diabetes']
) as dag:

    check_data = PythonOperator(
        task_id='check_diabetes_data',
        python_callable=fetch_data_from_postgres
    )
