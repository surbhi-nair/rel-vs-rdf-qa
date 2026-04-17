import json
import argparse
import sys
from pathlib import Path

# Import logic from the first script
# Ensure evaluate_sparql_f1.py is in the same directory
try:
    from evaluate_sparql_f1 import (
        calculate_f1_score_strict, 
        compute_f1_robust, 
        to_tuples
    )
except ImportError:
    print("Error: Could not import 'evaluate_sparql_f1.py'.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_file",
        type=str,
        default="experiments/bird_minidev/results/10/predictions_executed.json",
        help="Path to input JSON containing Gold SQL, Pred SPARQL, and Pred SQL."
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="experiments/bird_minidev/results/10/f1_all_scores.json",
        help="Path to save output."
    )
    parser.add_argument("--db_id", type=str, default=None, help="Filter by DB ID")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)

    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Stats
    sums = {
        "sparql": {"strict": 0.0, "greedy": 0.0},
        "sql": {"strict": 0.0, "greedy": 0.0}
    }
    count = 0
    processed_data = []

    for item in data:
        # Filter
        if args.db_id and item.get("db_id") != args.db_id:
            continue

        # Check Order By (Support 'gold_sql' or old 'sql' key)
        gold_sql_str = item.get("gold_sql") or item.get("sql") or ""
        has_order_by = "order by" in gold_sql_str.lower()

        # Get Raw Outputs
        gold_out = item.get("gold_sql_output") or item.get("sqloutput")
        sparql_out = item.get("sparqloutput")
        pred_sql_out = item.get("predicted_sql_output")

        # --- PREPARE DATA ---
        
        # Strict Data (Raw)
        gold_strict = to_tuples(gold_out, round_floats=False)
        sparql_strict = to_tuples(sparql_out, round_floats=False)
        pred_sql_strict = to_tuples(pred_sql_out, round_floats=False)

        # Greedy Data (Rounded)
        gold_greedy = to_tuples(gold_out, round_floats=True)
        sparql_greedy = to_tuples(sparql_out, round_floats=True)
        pred_sql_greedy = to_tuples(pred_sql_out, round_floats=True)

        # --- COMPUTE SCORES ---

        # 1. SPARQL vs Gold
        s_strict = calculate_f1_score_strict(sparql_strict, gold_strict)
        s_greedy = compute_f1_robust(sparql_greedy, gold_greedy, has_order_by)

        # 2. Predicted SQL vs Gold
        q_strict = calculate_f1_score_strict(pred_sql_strict, gold_strict)
        q_greedy = compute_f1_robust(pred_sql_greedy, gold_greedy, has_order_by)

        # Store
        item["scores"] = {
            "sparql": {
                "strict": s_strict,
                "greedy": s_greedy
            },
            "sql": {
                "strict": q_strict,
                "greedy": q_greedy
            }
        }

        # Update Stats
        sums["sparql"]["strict"] += s_strict
        sums["sparql"]["greedy"] += s_greedy
        sums["sql"]["strict"] += q_strict
        sums["sql"]["greedy"] += q_greedy
        count += 1
        processed_data.append(item)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=4)

    # Print Summary
    if count > 0:
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"Total Questions: {count}")
        print("-" * 60)
        print(f"{'METRIC':<15} | {'PRED SQL':<12} | {'PRED SPARQL':<12}")
        print("-" * 60)
        print(f"{'Strict F1':<15} | {sums['sql']['strict']/count:.4f}       | {sums['sparql']['strict']/count:.4f}")
        print(f"{'Greedy F1':<15} | {sums['sql']['greedy']/count:.4f}       | {sums['sparql']['greedy']/count:.4f}")
        print("="*60)
    else:
        print("No data processed.")

if __name__ == "__main__":
    main()