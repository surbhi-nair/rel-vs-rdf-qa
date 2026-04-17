import json
import sqlite3
import pandas as pd
from pathlib import Path
import requests
import argparse

"""Execute gold SQL and predicted SPARQL queries and normalize outputs.
Reads results.json in the experiment folder, runs the SQL/SPARQL queries, and writes both outputs in results_executed.json.
Usage: python get_sql.py --exp_id <optional-experiment-id>
"""

BASE_RESULTS_DIR = Path("experiments/bird_minidev/results")
# BASE_RESULTS_DIR = Path("experiments/bird_minidev_basic/results") # TODO: comment this and uncomment the above line when you want to run on the semantic RML mapping results instead of the simpler ones
BASE_DB_DIR = Path("data/MINIDEV/dev_databases")
# QLEVER_URL = "http://tagus:9004/api"

# Mapping from db_id (kg) to QLEVER endpoint
QLEVER_ENDPOINTS = {
    "california_schools": "http://localhost:9002",
    "card_games": "http://localhost:9003",
    "codebase_community": "http://localhost:9004",
    "debit_card_specializing": "http://localhost:9005",
    "european_football_2": "http://localhost:9006",
    "financial": "http://localhost:9007",
    "formula_1": "http://localhost:9008",
    "student_club": "http://localhost:9009",
    "superhero": "http://localhost:9010",
    "thrombosis_prediction": "http://localhost:9011",
    "toxicology": "http://localhost:9012"
}

def get_qlever_url(db_id):
    """Return the QLEVER endpoint URL for the given db_id."""
    endpoint = QLEVER_ENDPOINTS.get(db_id)
    if endpoint:
        return endpoint + "/api"
    else:
        print(f"Warning: No endpoint found for db_id '{db_id}'")
        return None

def get_db_path(db_id):
    """Build the SQLite file path from db_id."""
    return BASE_DB_DIR / db_id / f"{db_id}.sqlite"


def run_sql_query(db_path, query):
    """Execute SQL query on the given SQLite db and return the result as a string."""
    db_path = Path(db_path)
    if not db_path.exists():
        print(f"DB path not found: {db_path}")
        return {"columns": [], "rows": [], "row_count": 0, "col_count": 0}

    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(query, conn)
        # df = df.where(pd.notnull(df), None)
        # Convert to list of dicts
        records = df.to_dict(orient="records")

        # Replace any NaN with None for JSON
        for row in records:
            for k, v in row.items():
                if pd.isna(v):
                    row[k] = None

        return {
            "columns": df.columns.tolist(),
            "rows": records,
            "row_count": len(records),
            "col_count": len(df.columns)
        }
    except Exception as e:
        print(f"Error executing SQL on {db_path}: {e}")
        return {"columns": [], "rows": [], "row_count": 0, "col_count": 0}

def run_sparql_query(sparql_query, db_id, timeout=60):
    endpoint = get_qlever_url(db_id)
    if not sparql_query or not endpoint:
        return None
    try:
        resp = requests.get(endpoint, params={"query": sparql_query}, timeout=timeout)
        resp.raise_for_status()
        # return a compact pretty JSON string (so it's similar to SQL string output)
        # return json.dumps(resp.json(), indent=2)
        return resp.json()
    except Exception as e:
        print(f"Error executing SPARQL against {endpoint}: {e}")
        return None

def parse_sparql_json(sparql_json):
    if not sparql_json:
        # return empty structure so downstream code always gets a dict
        return {"columns": [], "rows": [], "row_count": 0, "col_count": 0}

    # handle ASK queries which return {"boolean": true/false}
    if "boolean" in sparql_json:
        rows = [{"boolean": bool(sparql_json["boolean"]) }]
        return {"columns": ["boolean"], "rows": rows, "row_count": len(rows), "col_count": 1}

    columns = sparql_json.get("head", {}).get("vars", [])
    rows = []

    bindings = sparql_json.get("results", {}).get("bindings", []) or []
    for b in bindings:
        if not isinstance(b, dict):
            # skip invalid/None binding entries
            continue
        row = {}
        for col in columns:
            cell = b.get(col)
            if not cell:
                row[col] = None
                continue
            val = cell.get("value")
            dt = cell.get("datatype", "")
            try:
                if "int" in dt:
                    val = int(val)
                elif "decimal" in dt or "float" in dt or "double" in dt:
                    val = float(val)
            except Exception:
                # keep original string if conversion fails
                pass
            row[col] = val
        rows.append(row)

    return {"columns": columns, "rows": rows, "row_count": len(rows), "col_count": len(columns)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exp_id",
        type=str,
        default=None,
        help="Experiment ID: subfolder name under experiments/bird_minidev_basic/results (e.g., '1', 'test'). If not provided, uses base path."
    )
    args = parser.parse_args()

    exp_id = args.exp_id

    # Determine results directory
    if exp_id:
        results_dir = BASE_RESULTS_DIR / exp_id
        results_dir.mkdir(parents=True, exist_ok=True)
    else:
        results_dir = BASE_RESULTS_DIR

    INPUT_JSON = results_dir / "results.json"
    OUTPUT_JSON = results_dir / "results_executed.json"

    if exp_id:
        print(f"Using experiment folder: {results_dir}")

    # Load existing results
    with open(INPUT_JSON, "r") as f:
        data = json.load(f)

    updated_results = []

    for item in data:
        qid = item["question_id"]
        db_id = item["db_id"]
        sql_query = item.get("sql")
        sparql_query = item.get("sparql")

        # --- SQL part: run if missing and query present ---
        if "sqloutput" in item and item["sqloutput"] is not None:
            print(f"Skipping SQL for QID {qid} (sqloutput already present)")
        elif sql_query:
            db_path = get_db_path(db_id)
            if not db_path.exists():
                print(f"DB path not found for db_id: {db_id}, skipping SQL for QID {qid}")
                item["sqloutput"] = None
            else:
                print(f"Running SQL for QID {qid} on DB {db_id}")
                item["sqloutput"] = run_sql_query(db_path, sql_query)
        else:
            # ensure key exists
            item.setdefault("sqloutput", None)

        # --- SPARQL part: run if missing and query present ---
        if "sparqloutput" in item and item["sparqloutput"] is not None:
            print(f"Skipping SPARQL for QID {qid} (sparqloutput already present)")
        elif sparql_query:
            print(f"Running SPARQL for QID {qid}")
            # item["sparqloutput"] = run_sparql_query(sparql_query)
            raw_sparql = run_sparql_query(sparql_query, db_id)
            # item["sparqloutput_raw"] = raw_sparql
            item["sparqloutput"] = parse_sparql_json(raw_sparql)
        else:
            item.setdefault("sparqloutput", None)

        updated_results.append(item)

    # Save updated results
    with open(OUTPUT_JSON, "w") as f:
        json.dump(updated_results, f, indent=4)

    print(f"\nUpdated results saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()