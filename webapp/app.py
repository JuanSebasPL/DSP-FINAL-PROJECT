# webapp/app.py
from pathlib import Path
import os
import streamlit as st
from dotenv import load_dotenv

def load_environment():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    return {
        "ENV_NAME": os.getenv("ENV_NAME", "local"),
        "API_CLIENT_MODE": os.getenv("API_CLIENT_MODE", "FAKE"),
        "FASTAPI_URL": os.getenv("FASTAPI_URL", ""),
    }

st.set_page_config(page_title="DSP WebApp", page_icon="🧩", layout="wide")
settings = load_environment()

# Sidebar status
st.sidebar.title("DSP — WebApp")
st.sidebar.caption("Mini ML app in production")
st.sidebar.markdown("### Environment")
st.sidebar.write(f"ENV_NAME: `{settings['ENV_NAME']}`")
st.sidebar.write(f"API_CLIENT_MODE: `{settings['API_CLIENT_MODE']}`")
st.sidebar.write(f"FASTAPI_URL: `{settings['FASTAPI_URL'] or 'NOT SET'}`")

st.title("🧩 DSP — ML App")
st.write("Use the sidebar to navigate to pages. Prediction + Past Predictions work in FAKE mode.")

