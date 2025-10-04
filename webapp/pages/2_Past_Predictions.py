# webapp/pages/2_Past_Predictions.py

import datetime as dt
import streamlit as st
import pandas as pd

from api_client import get_client

@st.cache_resource
def _client():
    return get_client()

client = _client()

st.title("🕓 Past Predictions")
st.caption("Filter by date and source. (Data is fake for now so you can practice.)")

# --- Filters (simple) ---
today = dt.date.today()
default_start = today - dt.timedelta(days=1)

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    start_date = st.date_input("Start date", value=default_start)
with col2:
    end_date = st.date_input("End date", value=today)
with col3:
    source = st.selectbox("Source", options=["all", "webapp", "scheduled"], index=0)

if st.button("Fetch"):
    with st.spinner("Loading history..."):
        df = client.get_past_predictions(
            start=str(start_date),
            end=str(end_date),
            source=source,
        )

    if df.empty:
        st.info("No predictions found for this filter.")
    else:
        st.success(f"Found {len(df)} row(s).")
        # Show newest first
        st.dataframe(df, use_container_width=True)

        # Quick summaries (nice for demo)
        with st.expander("Quick stats"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Average prediction", f"{df['prediction'].mean():.2f}")
            with col_b:
                st.metric("Webapp vs Scheduled",
                          f"{(df['source'] == 'webapp').sum()} / {(df['source'] == 'scheduled').sum()}")
