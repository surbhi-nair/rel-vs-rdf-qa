import json
import os
from typing import List

def generate_remaining_inputs(previous_results_paths: List[str], original_dataset_path: str, output_path: str):
    """
    Creates a new dataset file containing only questions that haven't been processed yet,
    aggregating completed IDs from multiple result files.
    """
    
    # 1. Load the Completed IDs from ALL provided files
    completed_pairs = set() # using a set for O(1) lookups
    
    print(f"Scanning {len(previous_results_paths)} result files for completed questions...")

    for result_file in previous_results_paths:
        if os.path.exists(result_file):
            try:
                with open(result_file, 'r') as f:
                    results_data = json.load(f)
                    
                # Navigate to the specific structure: ids -> final_SQL -> [correct/incorrect/error]
                final_sql_stats = results_data.get("ids", {}).get("final_SQL", {})
                
                count_in_file = 0
                for status in ["correct", "incorrect", "error"]:
                    if status in final_sql_stats:
                        for entry in final_sql_stats[status]:
                            # Entry format is [db_id, question_id]
                            if len(entry) >= 2:
                                db_id = entry[0]
                                q_id = entry[1]
                                completed_pairs.add((str(db_id), int(q_id)))
                                count_in_file += 1
                
                print(f"  - {result_file}: Found {count_in_file} entries.")
                
            except json.JSONDecodeError:
                print(f"  - Warning: {result_file} is empty or invalid JSON. Skipping.")
        else:
            print(f"  - Warning: File not found at {result_file}. Skipping.")

    print(f"Total unique processed questions found: {len(completed_pairs)}")

    # 2. Load the Original Dataset
    try:
        with open(original_dataset_path, 'r') as f:
            original_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Original dataset file not found at {original_dataset_path}")
        return

    # 3. Filter the Dataset
    remaining_questions = []
    
    for item in original_data:
        q_id = int(item.get("question_id"))
        db_id = str(item.get("db_id"))
        
        # Check if this pair exists in our combined set of completed work
        if (db_id, q_id) not in completed_pairs:
            remaining_questions.append(item)

    # 4. Save the New Input File
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(remaining_questions, f, indent=4)
        
    print(f"Created '{output_path}' with {len(remaining_questions)} questions remaining (out of {len(original_data)} total).")

# --- Configuration ---
if __name__ == "__main__":
    # Add all your result JSON files to this list
    PREVIOUS_RESULTS_FILES = [
        "results/dev/CHESS_IR_CG_UT/mini_dev_sqlite/2026-01-25T17:21:19.357167/-statistics.json",
        "results/dev/CHESS_IR_CG_UT/remaining_minidev/2026-01-25T23:01:02.705158/-statistics.json",
        "results/dev/CHESS_IR_CG_UT/remaining_minidev/2026-01-26T17:20:22.573920/-statistics.json"
    ]
    
    ORIGINAL_DATASET_FILE = "/local/data-ssd/nairs/masters_project/data/MINIDEV/mini_dev_sqlite.json"
    NEW_INPUT_FILE = "data/dev/remaining_minidev.json"

    generate_remaining_inputs(PREVIOUS_RESULTS_FILES, ORIGINAL_DATASET_FILE, NEW_INPUT_FILE)