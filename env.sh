#!/usr/bin/env bash
set -euo pipefail

# Project root (this folder)
export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Python venv
export VENV_PATH="$PROJECT_ROOT/.venv"
export PATH="$VENV_PATH/bin:$PATH"

# Airflow config
export AIRFLOW_HOME="$PROJECT_ROOT/airflow"
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="postgresql+psycopg2://admin:admin@localhost:5432/airflow_db"
export AIRFLOW__CORE__DAGS_FOLDER="$PROJECT_ROOT/airflow/dags"

# Ports
export API_PORT=8000
export STREAMLIT_PORT=8501
export AIRFLOW_PORT=8080
export PGADMIN_PORT=5051
export POSTGRES_PORT=5432

# Docker compose services you want
export DOCKER_SERVICES="postgres pgadmin"
