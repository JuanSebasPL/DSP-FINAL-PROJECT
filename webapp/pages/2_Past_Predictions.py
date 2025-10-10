# webapp/pages/2_Past_Predictions.py
"""
Past Predictions Page
=====================
View historical diabetes predictions with date and source filters.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
sys.path.append('..')
from api_client import DiabetesAPIClient


# Page configuration
st.set_page_config(
    page_title="Past Predictions",
    page_icon="",
    layout="wide"
)

st.title("Past Predictions")
st.markdown("View and filter historical diabetes predictions from the database.")

# Initialize API client
@st.cache_resource
def get_client():
    """Initialize and cache the API client."""
    return DiabetesAPIClient()

client = get_client()

# ============================================================================
# FILTERS SECTION
# ============================================================================
st.subheader("Filters")

col1, col2, col3 = st.columns(3)

with col1:
    # Date range filter
    st.markdown("**Date Range**")
    today = datetime.now().date()
    default_start = today - timedelta(days=7)  # Last 7 days
    
    start_date = st.date_input(
        "Start Date",
        value=default_start,
        max_value=today,
        help="Select the start date for filtering predictions"
    )

with col2:
    st.markdown("**&nbsp;**")  # Spacing
    end_date = st.date_input(
        "End Date",
        value=today,
        max_value=today,
        help="Select the end date for filtering predictions"
    )

with col3:
    # Source filter
    st.markdown("**Prediction Source**")
    source = st.selectbox(
        "Source",
        options=["all", "webapp", "scheduled"],
        index=0,
        help="Filter by prediction source"
    )

# Fetch button
if st.button("Fetch Predictions", use_container_width=True):
    # Convert dates to strings
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Validate date range
    if start_date > end_date:
        st.error("Start date cannot be after end date!")
    else:
        with st.spinner("Fetching predictions from database..."):
            try:
                # Call API
                df = client.get_past_predictions(
                    start_date=start_str,
                    end_date=end_str,
                    source=source
                )
                
                # Check if results exist
                if df.empty:
                    st.warning("No predictions found for the selected filters.")
                    st.info(f"**Filters applied:**\n- Date range: {start_str} to {end_str}\n- Source: {source}")
                else:
                    # Display summary metrics
                    st.success(f"Found {len(df)} predictions!")
                    
                    # Summary statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Predictions", len(df))
                    
                    with col2:
                        high_risk = (df["prediction"] == 1).sum()
                        st.metric("High Risk", high_risk)
                    
                    with col3:
                        low_risk = (df["prediction"] == 0).sum()
                        st.metric("Low Risk", low_risk)
                    
                    with col4:
                        if source == "all":
                            webapp_count = (df["source"] == "webapp").sum()
                            scheduled_count = (df["source"] == "scheduled").sum()
                            st.metric("Webapp / Scheduled", f"{webapp_count} / {scheduled_count}")
                        else:
                            st.metric("Source", source.capitalize())
                    
                    st.markdown("---")
                    
                    # Display results table
                    st.subheader("Prediction History")
                    
                    # Format timestamp for better readability
                    if "timestamp" in df.columns:
                        df_display = df.copy()
                        df_display["timestamp"] = pd.to_datetime(df_display["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        df_display = df
                    
                    # Reorder columns for better display
                    column_order = ["timestamp", "prediction", "source"]
                    feature_columns = [col for col in df_display.columns if col not in column_order]
                    final_columns = column_order + feature_columns
                    
                    # Filter to only existing columns
                    final_columns = [col for col in final_columns if col in df_display.columns]
                    df_display = df_display[final_columns]
                    
                    # Display with color coding
                    st.dataframe(
                        df_display,
                        use_container_width=True,
                        height=400
                    )
                    
                    # Download option
                    st.markdown("---")
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download as CSV",
                        data=csv,
                        file_name=f"past_predictions_{start_str}_to_{end_str}.csv",
                        mime="text/csv"
                    )
                    
                    # Additional insights
                    with st.expander("Quick Insights"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Risk Distribution**")
                            risk_counts = df["prediction"].value_counts()
                            risk_df = pd.DataFrame({
                                "Risk Level": ["Low Risk (0)", "High Risk (1)"],
                                "Count": [risk_counts.get(0, 0), risk_counts.get(1, 0)]
                            })
                            st.dataframe(risk_df, hide_index=True)
                        
                        with col2:
                            if source == "all":
                                st.markdown("**Source Distribution**")
                                source_counts = df["source"].value_counts()
                                st.dataframe(source_counts, use_container_width=True)
                            else:
                                st.markdown("**Average Glucose Level**")
                                if "Glucose" in df.columns:
                                    avg_glucose = df["Glucose"].mean()
                                    st.metric("Average", f"{avg_glucose:.1f} mg/dL")
                
            except Exception as e:
                st.error(f"Failed to fetch predictions: {str(e)}")
                st.info("Make sure the FastAPI service is running and the database is accessible!")

# ============================================================================
# SIDEBAR INFO
# ============================================================================
with st.sidebar:
    st.header("ℹAbout This Page")
    st.markdown("""
    This page displays historical predictions stored in the database.
    
    **Features:**
    - Filter by date range
    - Filter by source (webapp or scheduled)
    - View detailed prediction history
    - Download results as CSV
    
    **Sources:**
    - **webapp**: Predictions made through this UI
    - **scheduled**: Predictions from automated Airflow jobs
    """)
    
    st.markdown("---")
    
    st.markdown("**Quick Tips:**")
    st.markdown("""
    - Use a narrower date range for faster results
    - Filter by source to see specific prediction types
    - Download data for further analysis
    """)
    
    st.markdown("---")
    
    # API Status check
    if st.button("Check API Status"):
        with st.spinner("Checking..."):
            try:
                status = client.health_check()
                st.success("API is running!")
                st.json(status)
            except Exception as e:
                st.error("API is not responding")
                st.error(str(e))