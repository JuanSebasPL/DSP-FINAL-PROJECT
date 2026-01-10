HealthVision – Diabetes Prediction System

End-to-End Data Science in Production Project

An end-to-end machine learning system for diabetes risk prediction, focusing on production engineering, including APIs, databases, orchestration, automation, and reproducibility.

This project was developed as part of the Data Science in Production course.

Project Overview

The system predicts diabetes risk (0/1) from patient health indicators and demonstrates how a real-world ML system operates in production.

Key Features

FastAPI backend for predictions & data persistence

Streamlit frontend for user interaction

PostgreSQL database for storing predictions and statistics

Apache Airflow for data ingestion & scheduled predictions

Docker Compose for infrastructure services

Production-grade startup script (manage.sh) to run everything cleanly

Tech Stack
Component	Technology
UI	Streamlit
API	FastAPI + Uvicorn
ML	scikit-learn
Database	PostgreSQL
Orchestration	Apache Airflow
Infrastructure	Docker + Docker Compose
Language	Python 3.12
Project Structure
DSP-FINAL-PROJECT/
├── api/                    # FastAPI backend
├── webapp/                 # Streamlit UI
├── airflow/                # Airflow home (DAGs, logs, config)
│   └── dags/
├── data/
│   ├── raw_data/           # Incoming CSVs
│   ├── good_data/          # Validated data
│   └── bad_data/           # Invalid data
├── db/
│   └── master_sql          # Database schema
├── docker-compose.yaml     # Postgres + pgAdmin
├── .venv/                  # Python virtual environment
├── manage.sh               # Professional service manager
├── env.sh                  # Shared environment variables
└── README.md

Dataset

Pima Indians Diabetes Dataset
https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database

Features

Pregnancies

Glucose

BloodPressure

SkinThickness

Insulin

BMI

DiabetesPedigreeFunction

Age

Target: Outcome (0 = No Diabetes, 1 = Diabetes)

How to Run Everything (Recommended Way)

⚠️ This project should always be started using manage.sh
It automatically stops conflicting services and avoids port issues.

1️⃣ Prerequisites

Docker Desktop (with WSL integration enabled)

Python 3.12

Virtual environment already created at .venv/

2️⃣ Start all services

From the project root:

./manage.sh start


This will automatically:

Start Docker services (Postgres + pgAdmin)

Start FastAPI (port 8000)

Start Streamlit (port 8501)

Start Airflow webserver & scheduler (port 8080)

Kill any conflicting processes on used ports

Write logs to ./logs/

3️⃣ Check service status
./manage.sh status


Expected output:

✅ api running
✅ streamlit running
✅ airflow_webserver running
✅ airflow_scheduler running

4️⃣ Access the applications
Service	URL
FastAPI	http://localhost:8000

Streamlit UI	http://localhost:8501

Airflow UI	http://localhost:8080

pgAdmin	http://localhost:5051

PostgreSQL	localhost:5432
5️⃣ Stop everything
./manage.sh stop

6️⃣ Restart cleanly (recommended if something breaks)
./manage.sh restart

Airflow Pipelines
1️⃣ Data Ingestion DAG

DAG ID: data_ingestion_pipeline

Reads one CSV per run from data/raw_data/

Validates schema & values

Moves files to good_data/ or bad_data/

Sends file statistics to the API

Saves statistics to PostgreSQL (file_statistics table)

2️⃣ Prediction DAG

DAG ID: process_success_files_dag

Detects new files only

Calls /predict?source=scheduled

Stores predictions in PostgreSQL (diabetes_data table)

Skips execution if no new data (expected production behavior)

Database Tables
diabetes_data (Predictions)

Stores:

Input features

Prediction result

Source (webapp or scheduled)

Timestamp

file_statistics

Stores:

Filename

Total rows

Valid / invalid rows

Validation errors

Timestamp

Logs & Debugging

All logs are written to:

./logs/


Useful commands:

tail -f logs/api.log
tail -f logs/streamlit.log
tail -f logs/airflow_webserver.log
tail -f logs/airflow_scheduler.log

Common Issues & Fixes
Port already in use

✔ Automatically handled by manage.sh

DAG shows “skipped”

✔ Normal behavior — no new data to process

Database tables missing

✔ Recreated using db/master_sql

Team – HealthVision

Juan Sebastian Pereira Lopez

Iqra Javed

Kaviyarasan Arul Jothi

Basit Ur Rehman

Course

Data Science in Production

Final Notes

This project demonstrates:

Production-ready ML architecture

Automated pipelines

Robust error handling

Reproducible infrastructure

Clean operational workflows



To run Grafana:


- First, see what the service is called in compose:

docker compose config --services


- If grafana appears in the list, start it:

docker compose up -d grafana


- If the service name is different (like grafana-service), run:

docker compose up -d <service_name>