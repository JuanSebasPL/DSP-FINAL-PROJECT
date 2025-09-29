# Data Science in Production - Project Proposal

## Group Name  
**HealthVision**

## Group Members  
• Juan Sebastain Pereira Lopez
• iqra javedd
• Kaviyarasan Arul Jothi
• Basit Ul Rehman

---

## Project Subject  

### Chosen Use Case  
Prediction of diabetes presence in patients based on health indicators.  

### Dataset Link and Description  
We will use the **Pima Indians Diabetes Database** from Kaggle:  
[https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database](https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database)  

This dataset contains medical diagnostic measurements to determine whether a patient is likely to have diabetes. It includes numerical health indicators such as glucose concentration, blood pressure, BMI, and age. The target variable is binary (diabetes or not).  

**Includes multiple data types:**  
  - **Numeric:** medical measurements.  
  - **Boolean:** target variable (has diabetes or not).  
  - **String:** we will add an artificial patient identifier column for compliance with assignment requirements.  

---

## Columns Categorized by Type  

### Numeric  
- `Pregnancies` (Number of times pregnant)  
- `Glucose` (Plasma glucose concentration)  
- `BloodPressure` (Diastolic blood pressure)  
- `SkinThickness` (Triceps skin fold thickness)  
- `Insulin` (2-Hour serum insulin)  
- `BMI` (Body mass index)  
- `DiabetesPedigreeFunction` (Diabetes pedigree function)  
- `Age` (Age in years)  

### Boolean  
- `Outcome` (1 = diabetes, 0 = no diabetes)  

### String  
- `PatientID` (artificial string column generated from row index, e.g., “P001”, “P002”, …)  

---
