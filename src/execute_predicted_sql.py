import json
import sqlite3
import pandas as pd
from pathlib import Path
import argparse
import sys

# ================= CONFIGURATION =================
# Path to the output from the previous script (Question + Gold SQL + Predicted SQL)
INPUT_PREDICTIONS_FILE = "CHESS/results/dev/combined/no_evidence/final_results_with_predictions.json"

# Path to the file containing Gold SQL outputs & SPARQL outputs
INPUT_EXECUTED_FILE = "experiments/bird_minidev/results/10/results_executed.json"

# Final Output Path
FINAL_OUTPUT_FILE = "experiments/bird_minidev/results/10/predictions_executed.json"

# Database Directory
BASE_DB_DIR = Path("data/MINIDEV/dev_databases")
# =================================================

def get_db_path(db_id):
    """Build the SQLite file path from db_id."""
    return BASE_DB_DIR / db_id / f"{db_id}.sqlite"

def run_sql_query(db_path, query):
    """
    Execute SQL query on the given SQLite db and return the result 
    formatted exactly like the bird-bench format.
    """
    db_path = Path(db_path)
    
    # 1. Error Handling: Missing DB
    if not db_path.exists():
        # print(f"Error: DB path not found: {db_path}")
        return None

    # 2. Error Handling: Empty Query
    if not query:
         return None

    try:
        with sqlite3.connect(db_path) as conn:
            # Use pandas for robust reading
            df = pd.read_sql_query(query, conn)
        
        # Convert to list of dicts
        records = df.to_dict(orient="records")

        # Replace NaN with None (JSON standard)
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
        # Return None or empty structure on failure? 
        # Usually None implies "Execution Failed"
        return None

def load_json(filepath):
    if not Path(filepath).exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    print("Loading input files...")
    
    # 1. Load Prediction Data (Source for: predicted_sql, difficulty)
    pred_data_list = load_json(INPUT_PREDICTIONS_FILE)
    # Convert to map for O(1) lookup
    pred_map = {str(item["question_id"]): item for item in pred_data_list}
    
    # 2. Load Executed Data (Source for: id, db_id, question, gold_sql, sparql, output)
    executed_data_list = load_json(INPUT_EXECUTED_FILE)
    
    final_results = []
    processed_ids = set()

    print(f"Processing {len(executed_data_list)} items from executed results...")

    for exec_item in executed_data_list:
        q_id = str(exec_item.get("question_id"))
        
        # skip duplicates
        if q_id in processed_ids:
            continue
            
        # Retrieve matching prediction item
        pred_item = pred_map.get(q_id, {})

        # Extract values needed for execution
        db_id = exec_item.get("db_id")
        predicted_sql = pred_item.get("predicted_sql")

        # --- EXECUTE PREDICTED SQL ---
        predicted_sql_output = None
        if predicted_sql and db_id:
            db_path = get_db_path(db_id)
            predicted_sql_output = run_sql_query(db_path, predicted_sql)

        # --- BUILD FINAL DICTIONARY (Enforcing Order) ---
        # Order: 
        # 1. question_id, db_id, question (from executed)
        # 2. gold_sql (renamed)
        # 3. predicted_sql (from predictions)
        # 4. sparql (from executed)
        # 5. gold_sql_output (renamed)
        # 6. predicted_sql_output (calculated)
        # 7. sparqloutput (from executed)
        # 8. difficulty (from predictions)

        final_item = {
            "question_id": exec_item.get("question_id"),
            "db_id":       exec_item.get("db_id"),
            "question":    exec_item.get("question"),
            
            "gold_sql":      exec_item.get("sql"),             # Renamed from 'sql'
            "predicted_sql": predicted_sql,                    # From prediction file
            
            "sparql":        exec_item.get("sparql"),
            
            "gold_sql_output":      exec_item.get("sqloutput"), # Renamed from 'sqloutput'
            "predicted_sql_output": predicted_sql_output,       # Calculated above
            "sparqloutput":         exec_item.get("sparqloutput"),
            
            "difficulty":    pred_item.get("difficulty")        # From prediction file
        }

        final_results.append(final_item)
        processed_ids.add(q_id)

    # Save output
    print(f"Saving {len(final_results)} merged entries to {FINAL_OUTPUT_FILE}...")
    with open(FINAL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=4)

    print("Done.")

if __name__ == "__main__":
    main()