#!/usr/bin/env python3
"""
CSV File Generator
==================
Creates 1000 CSV files with 10 random rows each.
"""

import pandas as pd
import os


SOURCE_CSV = "/mnt/c/Users/BRK/Downloads/archive (1)/diabetes.csv"


OUTPUT_DIR = "/mnt/c/Users/BRK/Downloads/generated_csv_files"


NUM_FILES = 1000


ROWS_PER_FILE = 10

FILE_PREFIX = "diabetes_batch"


def generate_csv_files():
    """Generate multiple CSV files with random rows."""
    
    print("=" * 60)
    print("CSV FILE GENERATOR")
    print("=" * 60)
    
    # Check if source file exists
    if not os.path.exists(SOURCE_CSV):
        print(f" ERROR: Source file not found!")
        print(f"   Looking for: {SOURCE_CSV}")
        return
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f" Source: {SOURCE_CSV}")
    print(f" Output: {OUTPUT_DIR}")
    
    # Read source CSV
    print(f"\n Reading source file...")
    df = pd.read_csv(SOURCE_CSV)
    print(f" Loaded {len(df)} rows")
    print(f"   Columns: {', '.join(df.columns)}")
    
    print(f"\n Generating {NUM_FILES} files with {ROWS_PER_FILE} rows each...")
    
    # Generate files
    for i in range(NUM_FILES):
        # Random sample (with replacement)
        sample = df.sample(n=ROWS_PER_FILE, replace=True)
        
        # Generate filename with leading zeros
        filename = f"{FILE_PREFIX}_{i+1:04d}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Save to CSV
        sample.to_csv(filepath, index=False)
        
        # Progress indicator every 100 files
        if (i + 1) % 100 == 0:
            print(f"    Created {i + 1}/{NUM_FILES} files...")
    
    print(f"\n SUCCESS!")
    print(f"   Created {NUM_FILES} CSV files in: {OUTPUT_DIR}")
    print(f"   Each file has {ROWS_PER_FILE} random rows")
    
    # Show sample files
    print(f"\n First 5 files created:")
    files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.csv')])[:5]
    for f in files:
        filepath = os.path.join(OUTPUT_DIR, f)
        size = os.path.getsize(filepath)
        print(f"   - {f} ({size} bytes)")
    
    print(f"\n To use these files in Airflow:")
    print(f"   Move them to: data/raw_data/")
    print(f"   Command: mv {OUTPUT_DIR}/*.csv data/raw_data/")

if __name__ == "__main__":
    generate_csv_files()
