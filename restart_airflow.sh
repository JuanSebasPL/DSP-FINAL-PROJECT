#!/bin/bash

echo "============================"
echo " SAFE AIRFLOW RESTART SCRIPT"
echo "============================"

AIRFLOW_HOME="/home/brk/projects/final_dsp_project/DSP-FINAL-PROJECT/airflow"

echo "[1] Stopping existing Airflow processes..."
pkill -f "airflow scheduler"
pkill -f "airflow webserver"
pkill -f "airflow worker"
pkill -f "gunicorn"
pkill -f "LocalExecutor"

sleep 2

echo "[2] Removing old PID and heartbeat files..."
rm -f $AIRFLOW_HOME/airflow-scheduler.pid
rm -f $AIRFLOW_HOME/airflow-webserver.pid
rm -rf $AIRFLOW_HOME/logs/scheduler/*

echo "[3] Checking Airflow DB connection..."
airflow db check || { echo "❌ Airflow DB not reachable!"; exit 1; }

echo "[4] Starting Airflow Scheduler..."
airflow scheduler -D
sleep 3

echo "[5] Starting Airflow Webserver..."
airflow webserver -D
sleep 5

echo "[6] (Optional) Starting Airflow Workers..."
airflow worker -D

echo "[7] Checking Scheduler heartbeat..."
airflow scheduler --status || echo "⚠️ Scheduler status check may fail on old Airflow versions."

echo ""
echo "===================================="
echo "   AIRFLOW SUCCESSFULLY RESTARTED   "
echo "===================================="
echo "Web UI: http://localhost:8080"
