#!/usr/bin/env python3
import os
import duckdb

# Configuration
DB_PATH = 'data/duckdb/hackathon.duckdb'
OUTPUT_DIR = 'data/csv'
SCHEMA = 'marts'

def export_marts():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at '{DB_PATH}'")
        print("Please run 'dbt run' first to build the database.")
        return

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Connecting to DuckDB database: {DB_PATH}")
    conn = duckdb.connect(DB_PATH)

    # Fetch all table names in the 'marts' schema
    query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{SCHEMA}'"
    tables = [row[0] for row in conn.execute(query).fetchall()]

    if not tables:
        print(f"No tables found in schema '{SCHEMA}'. Please ensure your dbt models ran successfully.")
        return

    print(f"Found {len(tables)} tables in schema '{SCHEMA}' to export:")
    for t in tables:
        print(f" - {t}")

    print("\nStarting export...")
    for table in tables:
        csv_file_path = os.path.join(OUTPUT_DIR, f"{table}.csv")
        print(f"Exporting {SCHEMA}.{table} -> {csv_file_path} ...", end="", flush=True)
        
        try:
            # Run the COPY command in DuckDB to export to CSV
            conn.execute(f"COPY {SCHEMA}.{table} TO '{csv_file_path}' (HEADER, DELIMITER ',')")
            print(" [OK]")
        except Exception as e:
            print(f" [FAILED] - {e}")

    print("\nExport process completed successfully!")
    print(f"CSV files are saved in: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    export_marts()
