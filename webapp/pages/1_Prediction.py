# webapp/pages/1_Prediction.py
"""
Diabetes Prediction Page
========================
Allows users to make diabetes predictions in two ways:
1. Single prediction - Manual form entry
2. Batch prediction - CSV file upload
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import sys
sys.path.append('..')
from api_client import DiabetesAPIClient


# Page configuration
st.set_page_config(
    page_title="Diabetes Prediction",
    page_icon="",
    layout="wide"
)

st.title(" Diabetes Prediction")
st.markdown("Enter patient data manually or upload a CSV file to get diabetes risk predictions.")

# Initialize API client
@st.cache_resource
def get_client():
    """Initialize and cache the API client."""
    return DiabetesAPIClient()

client = get_client()

# Create tabs for single vs batch prediction
tab1, tab2 = st.tabs([" Single Prediction", " Batch Prediction (CSV)"])

#Single predction func
with tab1:
    st.subheader("Enter Patient Information")
    st.markdown("Fill in all 8 health indicators to get a diabetes risk prediction.")
    
    # Create a form for single prediction
    with st.form("single_prediction_form"):
        # Use columns for better layout
        col1, col2 = st.columns(2)
        
        with col1:
            pregnancies = st.number_input(
                "Pregnancies",
                min_value=0,
                max_value=20,
                value=1,
                help="Number of times pregnant (0-17 typical range)"
            )
            
            glucose = st.number_input(
                "Glucose (mg/dL)",
                min_value=0,
                max_value=300,
                value=120,
                help="Plasma glucose concentration (70-200 typical range)"
            )
            
            blood_pressure = st.number_input(
                "Blood Pressure (mm Hg)",
                min_value=0,
                max_value=150,
                value=80,
                help="Diastolic blood pressure (60-120 typical range)"
            )
            
            skin_thickness = st.number_input(
                "Skin Thickness (mm)",
                min_value=0,
                max_value=100,
                value=20,
                help="Triceps skin fold thickness (10-50 typical range)"
            )
        
        with col2:
            insulin = st.number_input(
                "Insulin (µU/mL)",
                min_value=0,
                max_value=900,
                value=80,
                help="2-Hour serum insulin (0-300 typical range)"
            )
            
            bmi = st.number_input(
                "BMI",
                min_value=0.0,
                max_value=70.0,
                value=25.0,
                step=0.1,
                format="%.1f",
                help="Body Mass Index (18.5-40 typical range)"
            )
            
            dpf = st.number_input(
                "Diabetes Pedigree Function",
                min_value=0.0,
                max_value=3.0,
                value=0.5,
                step=0.001,
                format="%.3f",
                help="Likelihood based on family history (0.1-2.0 typical range)"
            )
            
            age = st.number_input(
                "Age (years)",
                min_value=1,
                max_value=120,
                value=30,
                help="Patient age (21-81 typical range)"
            )
        
        # Submit button
        submitted = st.form_submit_button(" Predict", use_container_width=True)
        
        if submitted:
            # Create patient data dictionary
            patient_data = {
                "Pregnancies": int(pregnancies),
                "Glucose": int(glucose),
                "BloodPressure": int(blood_pressure),
                "SkinThickness": int(skin_thickness),
                "Insulin": int(insulin),
                "BMI": float(bmi),
                "DiabetesPedigreeFunction": float(dpf),
                "Age": int(age)
            }
            
            # Make prediction
            with st.spinner(" Making prediction..."):
                try:
                    # Call API
                    result_df = client.predict([patient_data])
                    
                    # Display results
                    st.success(" Prediction Complete!")
                    
                    # Show prediction result prominently
                    prediction = result_df.iloc[0]["prediction"]
                    if prediction == 1:
                        st.error(" **HIGH RISK**: This patient shows indicators of diabetes risk.")
                    else:
                        st.success(" **LOW RISK**: This patient shows low diabetes risk indicators.")
                    
                    # Display full results
                    st.subheader(" Detailed Results")
                    st.dataframe(result_df, use_container_width=True)
                    
                    # Display timestamp
                    timestamp = result_df.iloc[0].get("timestamp", "N/A")
                    st.info(f" Prediction made at: {timestamp}")
                    
                except Exception as e:
                    st.error(f" Prediction failed: {str(e)}")
                    st.info(" Make sure the FastAPI service is running!")


# Batch predic function
with tab2:
    st.subheader("Upload CSV File for Batch Predictions")
    st.markdown("""
    Upload a CSV file with patient data to get predictions for multiple patients at once.
    
    **Required columns:** `Pregnancies`, `Glucose`, `BloodPressure`, `SkinThickness`, 
    `Insulin`, `BMI`, `DiabetesPedigreeFunction`, `Age`
    """)
    
    # Sample CSV download
    st.markdown("###  Download Sample CSV Template")
    sample_data = {
        "Pregnancies": [6, 1, 8],
        "Glucose": [148, 85, 183],
        "BloodPressure": [72, 66, 64],
        "SkinThickness": [35, 29, 0],
        "Insulin": [0, 0, 0],
        "BMI": [33.6, 26.6, 23.3],
        "DiabetesPedigreeFunction": [0.627, 0.351, 0.672],
        "Age": [50, 31, 32]
    }
    sample_df = pd.DataFrame(sample_data)
    
    # Convert to CSV for download
    csv_buffer = io.StringIO()
    sample_df.to_csv(csv_buffer, index=False)
    csv_string = csv_buffer.getvalue()
    
    st.download_button(
        label=" Download Sample CSV",
        data=csv_string,
        file_name="diabetes_prediction_template.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="Upload a CSV file with patient data"
    )
    
    if uploaded_file is not None:
        try:
            # Read CSV
            df = pd.read_csv(uploaded_file)
            
            st.success(f" File uploaded successfully! Found {len(df)} rows.")
            
            # Show preview
            with st.expander(" Preview uploaded data"):
                st.dataframe(df.head(10), use_container_width=True)
            
            # Validate required columns
            required_columns = [
                "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
                "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
            ]
            
            # Normalize column names (case-insensitive)
            df.columns = df.columns.str.strip()
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f" Missing required columns: {', '.join(missing_columns)}")
                st.info("Please make sure your CSV has all required columns.")
            else:
                # Predict button
                if st.button(" Predict for All Patients", use_container_width=True):
                    with st.spinner(f" Making predictions for {len(df)} patients..."):
                        try:
                            # Convert DataFrame to list of dictionaries
                            rows = df[required_columns].to_dict('records')
                            
                            # Call API (single call for all rows!)
                            result_df = client.predict(rows)
                            
                            # Display results
                            st.success(f" Predictions complete for {len(result_df)} patients!")
                            
                            # Summary statistics
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                total = len(result_df)
                                st.metric("Total Predictions", total)
                            with col2:
                                high_risk = (result_df["prediction"] == 1).sum()
                                st.metric("High Risk", high_risk)
                            with col3:
                                low_risk = (result_df["prediction"] == 0).sum()
                                st.metric("Low Risk", low_risk)
                            
                            # Display results table
                            st.subheader(" Prediction Results")
                            st.dataframe(result_df, use_container_width=True)
                            
                            # Download results
                            result_csv = result_df.to_csv(index=False)
                            st.download_button(
                                label=" Download Results as CSV",
                                data=result_csv,
                                file_name=f"predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                            
                        except Exception as e:
                            st.error(f" Batch prediction failed: {str(e)}")
                            st.info(" Make sure the FastAPI service is running!")
        
        except Exception as e:
            st.error(f" Error reading CSV file: {str(e)}")
            st.info("Please make sure your file is a valid CSV format.")

#Side bar details
with st.sidebar:
    st.header(" About")
    st.markdown("""
    This prediction system uses machine learning to assess diabetes risk based on:
    - Medical history
    - Current health metrics
    - Family history indicators
    
    **Model trained on:** Pima Indians Diabetes Database
    """)
    
    st.markdown("---")
    
    # API Status check (optional)
    if st.button(" Check API Status"):
        with st.spinner("Checking..."):
            try:
                status = client.health_check()
                st.success(" API is running!")
                st.json(status)
            except Exception as e:
                st.error(" API is not responding")
                st.error(str(e))