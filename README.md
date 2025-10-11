# HealthVision – Diabetes Prediction System

**End-to-end ML system with Streamlit (UI), FastAPI (API), PostgreSQL (DB), and Airflow (automation).**

- **Course:** Data Science in Production  
- **Team:** HealthVision — Juan Sebastian Pereira Lopez, Iqra Javed, Kaviyarasan Arul Jothi, Basit Ur Rehman

---

## Overview
Predicts diabetes risk (0/1) from patient health indicators. Focus is on **production ops**: APIs, data pipelines, scheduling, persistence, and reproducibility.

**Dataset:** Pima Indians Diabetes — https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database

**Features:** `Pregnancies, Glucose, BloodPressure, SkinThickness, Insulin, BMI, DiabetesPedigreeFunction, Age`  
**Target:** `Outcome` (0/1)

---

## Tech Stack
- **UI:** Streamlit 1.50.0
- **API:** FastAPI 0.118.0 + Uvicorn 0.37.0
- **DB:** PostgreSQL + SQLAlchemy 1.4.x + psycopg2-binary 2.9.x
- **Pipelines:** Apache Airflow 2.10.3
- **ML:** scikit-learn 1.7.x, pandas 2.3.x, numpy 2.3.x
- **Python:** 3.12

---

## Quick Start

> Assumes `docker-compose` is available and a Python venv at `.venv/`.

```bash
cd ~/projects/final_dsp_project/DSP-FINAL-PROJECT
docker-compose up -d postgres pgadmin   # pgAdmin is optional
# wait ~10s for DB startup
2) Terminal 2 — FastAPI (Backend)
bash
Copy code
cd ~/projects/final_dsp_project/DSP-FINAL-PROJECT/api
source ../.venv/bin/activate
uvicorn main:app --reload --port 8000
# Keep this terminal open
3) Terminal 3 — Streamlit (Frontend)
bash
Copy code
cd ~/projects/final_dsp_project/DSP-FINAL-PROJECT
source .venv/bin/activate
streamlit run webapp/app.py
Verify
bash
Copy code
docker ps                          # should show postgres (+ pgadmin if enabled)
curl http://localhost:8000         # {"message":"Welcome to DSP API"}
# Streamlit opens at http://localhost:8501
Running Airflow (ETL & Scheduled Predictions)
Airflow orchestrates:

Ingestion DAG: reads ONE file per run from data/raw_data/, validates, moves to good_data/ or bad_data/.

Prediction DAG: checks good_data/ for new files and calls POST /predict?source=scheduled.

Local (no Docker)
bash
Copy code
# First time only
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init
airflow users create --username admin --firstname Admin --lastname User \
  --role Admin --email admin@example.com --password admin

# Run (two terminals)
airflow webserver -p 8080
airflow scheduler
# UI: http://localhost:8080  → enable your DAGs
Folders used by DAGs

bash
Copy code
data/raw_data/    # new incoming CSVs
data/good_data/   # validated for prediction
data/bad_data/    # rejected files
🔌 API Endpoints (FastAPI)
GET / → health: {"message": "Welcome to DSP API"}

POST /model/train → (optional) train/save model

POST /predict?source=webapp|scheduled

Body: {"data": [ { "pregnancies": ..., "glucose": ..., ... }, ... ] }

Returns: {"predictions": [...], "items": [{...,"timestamp","source"}]}

Persists to DB: features, prediction, timestamp, source.

📁 Project Structure (short)
bash
Copy code
DSP-FINAL-PROJECT/
├─ api/                 # FastAPI service
│  ├─ main.py
│  ├─ schemas/
│  └─ services/
├─ webapp/              # Streamlit app
│  ├─ app.py
│  └─ api_client.py
├─ dags/                # Airflow DAGs
│  ├─ process_new_files_dag.py
│  └─ prediction_dag.py
├─ data/                # raw/good/bad data folders
├─ models/              # saved model(s)
├─ requirements.txt
└─ docker-compose.yml   # postgres (+ pgadmin), airflow (if present)
 Minimal Troubleshooting
Port in use: change with --port (FastAPI) or update compose ports.

DB connect error: ensure DB_CONN_STRING in api/main.py matches docker-compose env.

No files processed: confirm CSVs in data/raw_data/ and DAGs are enabled.

Streamlit not opening: visit http://localhost:8501 manually.

 Notes
source query param is used to tag predictions: webapp (UI) vs scheduled (Airflow).

Each ingestion DAG run processes exactly one file to simulate streaming.

Grafana monitoring is optional and not required for grading.

© 2025 HealthVision
