import json
import os
import subprocess
from pathlib import Path

import duckdb

# Resolve project root based on the location of this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DB_PATH = PROJECT_ROOT / "data" / "duckdb" / "hackathon.duckdb"
MANIFEST_PATH = PROJECT_ROOT / "dbt" / "target" / "manifest.json"


def _connect():
    """Open a read-only DuckDB connection."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"DuckDB database not found: {DB_PATH}"
        )

    # Set file_search_path so DuckDB can resolve relative paths (like '../data/...')
    # exactly as dbt would when it compiled the views from the dbt/ directory.
    return duckdb.connect(
        str(DB_PATH),
        read_only=True,
        config={"file_search_path": str(PROJECT_ROOT / "dbt")}
    )


def query_duckdb(query: str) -> str:
    """
    Execute a read-only SQL query against DuckDB.

    Use this to investigate data quality issues:
    - verify anomalies
    - compare metrics
    - inspect NULLs
    - find duplicates
    - check row counts
    - investigate upstream data
    """
    forbidden = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "truncate ",
        "create ",
        "replace ",
        "copy ",
    ]

    normalized = query.strip().lower()

    if any(keyword in normalized for keyword in forbidden):
        return "ERROR: Only read-only SQL queries are allowed."

    try:
        con = _connect()

        try:
            result = con.sql(query).df()

            if result.empty:
                return "Query executed successfully but returned 0 rows."

            # Avoid returning huge datasets to the LLM.
            if len(result) > 100:
                result = result.head(100)

            return result.to_string(index=False)

        finally:
            con.close()

    except Exception as exc:
        return f"ERROR executing query: {exc}"


def list_tables() -> str:
    """
    List available tables and views in DuckDB.
    """
    query = """
        SELECT
            table_schema,
            table_name,
            table_type
        FROM information_schema.tables
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
        ORDER BY table_schema, table_name
    """

    return query_duckdb(query)


def get_schema(table_name: str) -> str:
    """
    Return the schema of a table.
    """

    safe_table_name = table_name.replace("'", "''")

    query = f"""
        SELECT
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_name = '{safe_table_name}'
        ORDER BY ordinal_position
    """

    return query_duckdb(query)


def get_dbt_lineage(model_name: str) -> str:
    """
    Return upstream and downstream dbt dependencies for a model.
    """

    if not os.path.exists(MANIFEST_PATH):
        print(f"Manifest not found at {MANIFEST_PATH}. Attempting to run dbt compile...")
        try:
            subprocess.run(["dbt", "compile", "--project-dir", str(PROJECT_ROOT / "dbt")], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            return (
                f"ERROR: dbt manifest not found at {MANIFEST_PATH}. "
                f"Attempted to run dbt compile but it failed: {e.stderr}"
            )
        except FileNotFoundError:
            return (
                f"ERROR: dbt manifest not found at {MANIFEST_PATH}. "
                "Attempted to run dbt compile, but the 'dbt' command was not found."
            )

    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as file:
            manifest = json.load(file)
    except Exception as exc:
        return f"ERROR reading dbt manifest: {exc}"

    target_node_id = None
    target_node = None

    for node_id, node_data in manifest.get("nodes", {}).items():
        if node_data.get("name") == model_name:
            target_node_id = node_id
            target_node = node_data
            break

    if target_node is None:
        return f"ERROR: dbt model '{model_name}' not found."

    upstream = target_node.get("depends_on", {}).get("nodes", [])

    downstream = []

    for node_id, node_data in manifest.get("nodes", {}).items():
        dependencies = node_data.get("depends_on", {}).get("nodes", [])

        if target_node_id in dependencies:
            downstream.append(
                node_data.get("name", node_id)
            )

    return json.dumps(
        {
            "model": model_name,
            "resource_type": target_node.get(
                "resource_type"
            ),
            "database": target_node.get("database"),
            "schema": target_node.get("schema"),
            "alias": target_node.get("alias"),
            "upstream_models": upstream,
            "downstream_models": downstream,
        },
        indent=2,
    )


def get_model_sql(model_name: str) -> str:
    """
    Return SQL for a dbt model.
    """

    if not os.path.exists(MANIFEST_PATH):
        print(f"Manifest not found at {MANIFEST_PATH}. Attempting to run dbt compile...")
        try:
            subprocess.run(["dbt", "compile", "--project-dir", str(PROJECT_ROOT / "dbt")], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            return (
                f"ERROR: dbt manifest not found at {MANIFEST_PATH}. "
                f"Attempted to run dbt compile but it failed: {e.stderr}"
            )
        except FileNotFoundError:
            return (
                f"ERROR: dbt manifest not found at {MANIFEST_PATH}. "
                "Attempted to run dbt compile, but the 'dbt' command was not found."
            )

    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as file:
            manifest = json.load(file)
    except Exception as exc:
        return f"ERROR reading dbt manifest: {exc}"

    for node_data in manifest.get("nodes", {}).values():

        if node_data.get("name") == model_name:

            compiled_code = node_data.get("compiled_code")

            if compiled_code:
                return compiled_code

            raw_code = node_data.get("raw_code")

            if raw_code:
                return raw_code

            return (
                f"No SQL available for model '{model_name}'."
            )

    return f"ERROR: dbt model '{model_name}' not found."


def get_dq_history(
    table_name: str,
    metric_column: str,
    date_column: str,
    days: int = 30,
) -> str:
    """
    Retrieve historical values of a metric.

    Use this to detect when an anomaly started.
    """

    allowed = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_."
    )

    for identifier in (
        table_name,
        metric_column,
        date_column,
    ):
        if (
            not identifier
            or not set(identifier) <= allowed
        ):
            return (
                f"ERROR: Invalid identifier: {identifier}"
            )

    if days < 1 or days > 365:
        return "ERROR: days must be between 1 and 365."

    query = f"""
        SELECT
            {date_column} AS metric_date,
            COUNT(*) AS row_count,
            SUM({metric_column}) AS metric_value,
            AVG({metric_column}) AS metric_average,
            MIN({metric_column}) AS metric_min,
            MAX({metric_column}) AS metric_max
        FROM {table_name}
        WHERE {date_column} >= CURRENT_DATE - INTERVAL '{days}' DAY
        GROUP BY 1
        ORDER BY 1
    """

    return query_duckdb(query)