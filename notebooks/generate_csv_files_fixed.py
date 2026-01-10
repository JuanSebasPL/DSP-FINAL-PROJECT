#!/usr/bin/env python3
import pandas as pd
import os

# Absolute project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE_CSV = os.path.join(BASE_DIR, "api", "models", "diabetes.csv")

# Write to the REAL project data folder (NOT inside airflow)
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw-data")

NUM_FILES = 50
ROWS_PER_FILE = 10
FILE_PREFIX = "diabetes_batch"


def generate_csv_files():
    print("=" * 60)
    print("CSV FILE GENERATOR")
    print("=" * 60)

    if not os.path.exists(SOURCE_CSV):
        print(f"ERROR: Source file not found: {SOURCE_CSV}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = pd.read_csv(SOURCE_CSV)
    print(f"Loaded {len(df)} rows from {SOURCE_CSV}")

    print(f"Generating {NUM_FILES} files...")

    for i in range(NUM_FILES):
        sample = df.sample(n=ROWS_PER_FILE, replace=True)
        filename = f"{FILE_PREFIX}_{i+1:04d}.csv"
        filepath = os.path.join(OUTPUT_DIR, filename)
        sample.to_csv(filepath, index=False)

        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{NUM_FILES} files...")

    print(f"\nSUCCESS! Created {NUM_FILES} files in {OUTPUT_DIR}/")


if __name__ == "__main__":
    generate_csv_files()
