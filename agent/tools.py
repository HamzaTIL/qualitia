import duckdb
import json
import os
import pandas as pd

DB_PATH = "data/duckdb/hackathon.duckdb"
MANIFEST_PATH = "dbt/target/manifest.json"

def query_duckdb(query: str) -> str:
    """Runs a SQL query against the DuckDB data warehouse and returns the result as a string.
    Use this to profile data, check row counts, or aggregate metrics.
    Example: SELECT * FROM mart_payment_profiles LIMIT 5;"""
    try:
        # Check if database exists
        if not os.path.exists(DB_PATH):
            return f"Error: Database not found at {DB_PATH}"
            
        con = duckdb.connect(DB_PATH, read_only=True)
        result = con.sql(query).df()
        con.close()
        
        if result.empty:
            return "Query executed successfully but returned 0 rows."
            
        # Return a nicely formatted string of the dataframe
        return result.to_string()
    except Exception as e:
        return f"Error executing query: {str(e)}"

def get_dbt_lineage(model_name: str) -> str:
    """Finds the upstream dependencies (parents) for a given dbt model name.
    Pass the model name without the .sql extension (e.g., 'mart_seller_sales')."""
    if not os.path.exists(MANIFEST_PATH):
        return "Error: dbt manifest.json not found. Please ensure dbt pipeline has been run or compiled."
    
    with open(MANIFEST_PATH, 'r') as f:
        manifest = json.load(f)
    
    # Find the specific model node
    target_node = None
    for node_id, node_data in manifest.get('nodes', {}).items():
        if node_data.get('name') == model_name:
            target_node = node_id
            break
            
    if not target_node:
        return f"Model '{model_name}' not found in dbt manifest. Are you sure it exists?"
        
    depends_on = manifest['nodes'][target_node].get('depends_on', {}).get('nodes', [])
    if not depends_on:
        return f"Model '{model_name}' has no upstream dependencies (it might be a raw source or seed)."
        
    return f"Model '{model_name}' directly depends on:\n- " + "\n- ".join(depends_on)
