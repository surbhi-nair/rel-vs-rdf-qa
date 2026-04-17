import json
import argparse
import sys
from pathlib import Path

# ==============================================================================
# 1. STRICT LOGIC (ORIGINAL BIRD-BENCH)
# ==============================================================================

def calculate_row_match_strict(predicted_row, ground_truth_row):
    """
    Calculate the matching percentage for a single row.
    Fixed to handle duplicates correctly without crashing.
    """
    total_columns = len(ground_truth_row)
    if total_columns == 0:
        return 0.0, 0.0, 0.0

    matches = 0
    element_in_pred_only = 0
    
    # Create a mutable copy to track "consumption"
    gt_temp = list(ground_truth_row)

    for pred_val in predicted_row:
        # FIX: Check gt_temp, NOT ground_truth_row
        if pred_val in gt_temp:
            matches += 1
            gt_temp.remove(pred_val)
        else:
            element_in_pred_only += 1
            
    # Any items remaining in gt_temp were missed
    element_in_truth_only = len(gt_temp)
    
    match_percentage = matches / total_columns
    pred_only_percentage = element_in_pred_only / total_columns
    truth_only_percentage = element_in_truth_only / total_columns
    
    return match_percentage, pred_only_percentage, truth_only_percentage


def calculate_f1_score_strict(predicted, ground_truth):
    """
    Calculate the F1 score based on sets of predicted results and ground truth.
    """
    if not predicted and not ground_truth:
        return 1.0

    # Drop duplicates for strict set comparison
    # (BIRD logic implies strictly matching SETS of rows, not bags)
    predicted_dedup = list(dict.fromkeys(predicted)) if predicted else []
    ground_truth_dedup = list(dict.fromkeys(ground_truth))

    match_scores = []
    pred_only_scores = []
    truth_only_scores = []

    for i, gt_row in enumerate(ground_truth_dedup):
        if i >= len(predicted_dedup):
            match_scores.append(0)
            truth_only_scores.append(1)
            continue
            
        pred_row = predicted_dedup[i]
        match_score, pred_only_score, truth_only_score = calculate_row_match_strict(
            pred_row, gt_row
        )
        match_scores.append(match_score)
        pred_only_scores.append(pred_only_score)
        truth_only_scores.append(truth_only_score)

    for i in range(len(predicted_dedup) - len(ground_truth_dedup)):
        match_scores.append(0)
        pred_only_scores.append(1)
        truth_only_scores.append(0)

    tp = sum(match_scores)
    fp = sum(pred_only_scores)
    fn = sum(truth_only_scores)

    precision = tp / (tp + fp) if tp + fp > 0 else 0
    recall = tp / (tp + fn) if tp + fn > 0 else 0

    f1_score = (
        2 * precision * recall / (precision + recall) if precision + recall > 0 else 0
    )
    return f1_score

# ==============================================================================
# 2. GREEDY LOGIC (ROBUST TO DUPLICATES, ORDER, AND EXTRA COLUMNS)
# ==============================================================================

def calculate_row_match_relaxed(pred_row, gold_row):
    """
    Matches rows but ignores extra columns in prediction (No Penalty).
    Uses 'consumption' logic to prevent >1.0 scores on duplicates.
    """
    total_columns = len(gold_row)
    if total_columns == 0:
        return 0.0, 0.0, 0.0

    # Create copy for consumption
    gold_remaining = list(gold_row) 
    matches = 0
    
    # Check for Matches
    for pred_val in pred_row:
        # CRITICAL CHECK: Ensure we don't count the same gold item twice
        if pred_val in gold_remaining:
            matches += 1
            gold_remaining.remove(pred_val) 
            
    element_in_truth_only = len(gold_remaining)

    match_percentage = matches / total_columns
    pred_only_percentage = 0.0 
    truth_only_percentage = element_in_truth_only / total_columns

    return match_percentage, pred_only_percentage, truth_only_percentage
    
def compute_f1_robust(pred_rows, gold_rows, has_order_by):
    """
    Computes F1 score with robustness.
    """
    if not pred_rows and not gold_rows: return 1.0
    if not pred_rows: return 0.0
    if not gold_rows: return 0.0

    # Deduplicate while preserving order
    pred_rows = list(dict.fromkeys(pred_rows))
    gold_rows = list(dict.fromkeys(gold_rows))

    match_scores = []
    truth_only_scores = []

    # --- STRATEGY 1: ORDER MATTERS (Index Alignment) ---
    if has_order_by:
        for i, g_row in enumerate(gold_rows):
            if i >= len(pred_rows):
                match_scores.append(0)
                truth_only_scores.append(1)
                continue
            
            p_row = pred_rows[i]
            match, _, truth_only = calculate_row_match_relaxed(p_row, g_row)
            match_scores.append(match)
            truth_only_scores.append(truth_only)
        
        # Penalize extra rows (missed alignments count as 0 match)
        for i in range(len(gold_rows), len(pred_rows)):
            match_scores.append(0)
            pass 

    # --- STRATEGY 2: ORDER IGNORED (Greedy Search) ---
    else:
        # We search for the best match for every Gold Row
        available_pred_indices = set(range(len(pred_rows)))
        
        for g_row in gold_rows:
            best_score = -1.0
            best_pred_idx = -1
            
            for p_idx in available_pred_indices:
                p_row = pred_rows[p_idx]
                match, _, _ = calculate_row_match_relaxed(p_row, g_row)
                
                if match > best_score:
                    best_score = match
                    best_pred_idx = p_idx
                    if best_score == 1.0: break # Optimization
            
            if best_pred_idx != -1:
                match_scores.append(best_score)
                truth_only_scores.append(1.0 - best_score)
                available_pred_indices.remove(best_pred_idx)
            else:
                match_scores.append(0.0)
                truth_only_scores.append(1.0)

    # Compute Final Score
    tp = sum(match_scores)
    fn = sum(truth_only_scores)
    fp = 0 

    precision = tp / (tp + fp) if tp + fp > 0 else 0
    recall = tp / (tp + fn) if tp + fn > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0

    return f1

# ==============================================================================
# 3. HELPERS
# ==============================================================================

def to_tuples(table, round_floats=False):
    """Converts the {"columns": [], "rows": []} dict to list of tuples."""
    if not table or "rows" not in table or "columns" not in table:
        return []

    cols = table["columns"]
    rows = table["rows"]

    out_list = []
    for r in rows:
        row_vals = []
        for c in cols:
            val = r.get(c)
            
            if round_floats and isinstance(val, (int, float)):
                # Round for Greedy
                row_vals.append(str(round(float(val), 2)))
            else:
                # Keep raw for Strict
                row_vals.append(val if val is not None else "None") 
        
        out_list.append(tuple(row_vals))
    return out_list

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exp_id", type=str, default=None)
    parser.add_argument("--db_id", type=str, default=None)
    args = parser.parse_args()

    # Paths
    base_dir = Path("experiments/bird_minidev/results")
    if args.exp_id:
        results_dir = base_dir / args.exp_id
    else:
        results_dir = base_dir
        
    input_file = results_dir / "results_executed.json"
    
    if args.db_id:
        # output_file = results_dir / "db_f1_scores" / f"results_f1_{args.db_id}.json"
        output_file = results_dir / f"results_f1_{args.db_id}.json"
    else:
        output_file = results_dir / "results_f1.json"

    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Stats
    sums = {"strict": 0.0, "greedy": 0.0}
    count = 0
    processed_data = []

    for item in data:
        # Filter
        if args.db_id and item.get("db_id") != args.db_id:
            continue

        # Check Order By
        gold_sql_str = item.get("sql", "") or ""
        has_order_by = "order by" in gold_sql_str.lower()

        # Get Data
        gold_out = item.get("sqloutput")
        sparql_out = item.get("sparqloutput")

        # 1. Strict F1 (Raw Data, Index Alignment)
        gold_strict = to_tuples(gold_out, round_floats=False)
        sparql_strict = to_tuples(sparql_out, round_floats=False)
        f1_strict = calculate_f1_score_strict(sparql_strict, gold_strict)

        # 2. Greedy F1 (Rounded, Smart Search)
        gold_greedy = to_tuples(gold_out, round_floats=True)
        sparql_greedy = to_tuples(sparql_out, round_floats=True)
        f1_greedy = compute_f1_robust(sparql_greedy, gold_greedy, has_order_by)

        # Save
        item["scores"] = {
            "strict": f1_strict,
            "greedy": f1_greedy
        }

        sums["strict"] += f1_strict
        sums["greedy"] += f1_greedy
        count += 1
        processed_data.append(item)

    # Output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=4)

    print(f"\nDone. Processed {count} questions.")
    if count > 0:
        print(f"Avg Strict F1: {sums['strict']/count:.4f}")
        print(f"Avg Greedy F1: {sums['greedy']/count:.4f}")

if __name__ == "__main__":
    main()