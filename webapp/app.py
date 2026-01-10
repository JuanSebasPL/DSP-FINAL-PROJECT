# webapp/app.py
"""
HealthVision - Diabetes Prediction System
==========================================
Main entry point for the Streamlit web application.

This is a simple landing page that introduces the app.
The actual functionality is in the pages/ folder:
- 1_Prediction.py: Make diabetes predictions
- 2_Past_Predictions.py: View prediction history
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="HealthVision - Diabetes Prediction",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main page content
st.title(" HealthVision - Diabetes Prediction System")

st.markdown("""
Welcome to **HealthVision**, an AI-powered diabetes prediction system!

##  What This App Does

This application helps predict diabetes risk based on patient health indicators using machine learning.

### Features:
- ** Make Predictions**: Enter patient data or upload a CSV file to get instant diabetes risk predictions
- ** View History**: Browse past predictions with flexible date and source filters
- ** ML-Powered**: Uses a trained diabetes prediction model on real medical data

### Navigation:
Use the **sidebar** on the left to navigate between:
1. **Prediction** - Make single or batch predictions
2. **Past Predictions** - View historical prediction data

---

## Quick Start

1. Click **"Prediction"** in the sidebar to make predictions
2. Enter patient health data manually OR upload a CSV file
3. View results instantly!

---

## Required Patient Data

For each prediction, you need these 8 health indicators:

| Feature | Description | Example Range |
|---------|-------------|---------------|
| **Pregnancies** | Number of times pregnant | 0-17 |
| **Glucose** | Plasma glucose concentration (mg/dL) | 0-200 |
| **Blood Pressure** | Diastolic blood pressure (mm Hg) | 0-122 |
| **Skin Thickness** | Triceps skin fold thickness (mm) | 0-99 |
| **Insulin** | 2-Hour serum insulin (µU/mL) | 0-846 |
| **BMI** | Body mass index (weight in kg/(height in m)²) | 0-67.1 |
| **Diabetes Pedigree Function** | Diabetes likelihood based on family history | 0.078-2.42 |
| **Age** | Age in years | 21-81 |

---

## About HealthVision

**Team:**
- Juan Sebastain Pereira Lopez
- Iqra Javed
- Kaviyarasan Arul Jothi
- Basit Ur Rehman

**Dataset:** [Pima Indians Diabetes Database](https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database)

---

###  Ready to Get Started?

Click **"Prediction"** in the sidebar to begin!
""")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>HealthVision - Data Science in Production Project</p>
        <p>Made with ❤️ using Streamlit, FastAPI, and Machine Learning</p>
    </div>
    """,
    unsafe_allow_html=True
)