import json
import os

# ================= CONFIGURATION =================
# List of paths to your prediction files
PREDICTION_FILES_1 = [
        "results/dev/CHESS_IR_CG_UT/mini_dev_sqlite/2026-01-25T17:21:19.357167/-predictions.json",
        "results/dev/CHESS_IR_CG_UT/remaining_minidev/2026-01-25T23:01:02.705158/-predictions.json",
        "results/dev/CHESS_IR_CG_UT/remaining_minidev/2026-01-26T17:20:22.573920/-predictions.json",
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T11:43:19.194613/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T12:05:45.226230/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T14:32:57.845402/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T14:40:39.015609/-predictions.json",
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T15:07:33.523260/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T15:24:26.748275/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T15:29:01.641260/-predictions.json",
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T16:07:41.630648/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T17:07:35.365769/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T18:39:02.423348/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T19:08:09.779057/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T19:38:35.609799/-predictions.json", 
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T20:16:18.510128/-predictions.json",
		"results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T14:09:32.681899/-predictions.json",
		"results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T14:32:08.661216/-predictions.json",
		"results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T16:21:48.320997/-predictions.json",
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T16:54:12.738394/-predictions.json",
		"results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T17:07:42.829216/-predictions.json", 
		"results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T17:26:11.828688/-predictions.json", 
		"results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T17:46:49.531420/-predictions.json",
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T17:57:19.844700/-predictions.json"

]

# without evidence:
PREDICTION_FILES = [
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-01T23:30:27.252809/-predictions.json", #1471
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-01T23:43:36.957090/-predictions.json", #1472
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:05:25.110523/-predictions.json", #1473
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:12:59.726863/-predictions.json", #1476
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:16:21.955136/-predictions.json", #1479
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-07T23:25:32.726328/-predictions.json", #358
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:01:27.347408/-predictions.json", #469
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:04:42.085556/-predictions.json", #368
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:09:28.238758/-predictions.json", #368
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:18:38.816311/-predictions.json", #368
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:23:57.621501/-predictions.json", #383
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:39:34.770011/-predictions.json", #466
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T12:06:41.709586/-predictions.json", #468
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T12:34:46.941227/-predictions.json", #472, 473
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T13:22:34.581056/-predictions.json", #472, 473
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T13:37:16.561357/-predictions.json", # 347, 349, 352, 291, 397, 402
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T14:37:07.202685/-predictions.json", # 750
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T14:56:30.771076/-predictions.json", # rest of only sparql correct ones(402, 750 above)
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T18:56:22.198034/-predictions.json", # 20 ques from only sql correct
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T17:53:13.042141/-predictions.json", # next 20 ques from only sql correct
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T18:48:19.582508/-predictions.json", # next 20 ques from only sql correct
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T21:00:18.231243/-predictions.json", # next 20 ques from only sql correct
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T22:13:58.173967/-predictions.json", # next 8 ques from only sql correct
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T22:59:13.319371/-predictions.json" # last 20 ques from only sql correct
]

# Path to the ground truth file
MINIDEV_SQLITE_PATH = "/local/data-ssd/nairs/masters_project/data/MINIDEV/mini_dev_sqlite.json"

# Output paths
MERGED_PREDICTIONS_OUTPUT = "results/dev/combined/no_evidence/merged_predictions.json"
FINAL_COMBINED_OUTPUT = "results/dev/combined/no_evidence/final_results_with_predictions.json"
# =================================================

def load_json(filepath):
    """Safely loads a JSON file."""
    if not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}")
        return {}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_prediction_sql(raw_sql):
    """
    Removes the appended metadata (e.g., '\t----- bird -----\t...') 
    from the prediction string.
    """
    if not raw_sql:
        return ""
    # Split by the tab character usually separating the SQL from metadata
    # Format: "SELECT ... \t----- bird -----\t..."
    return raw_sql.split('\t')[0].strip()

def main():
    # 1. Merge all prediction files into one dictionary
    all_predictions = {}
    print("Merging prediction files...")
    
    for pred_file in PREDICTION_FILES:
        data = load_json(pred_file)
        if isinstance(data, dict):
            # Update the master dictionary. 
            # Later files will overwrite earlier ones if question_ids overlap.
            all_predictions.update(data)
            print(f"Loaded {len(data)} predictions from {pred_file}")
        else:
            print(f"Skipping {pred_file}: Expected a dictionary, got {type(data)}")

    # Save the merged predictions raw file
    with open(MERGED_PREDICTIONS_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(all_predictions, f, indent=4)
    print(f"Saved merged predictions to: {MERGED_PREDICTIONS_OUTPUT}")

    # 2. Load Ground Truth Data
    minidev_data = load_json(MINIDEV_SQLITE_PATH)
    if not isinstance(minidev_data, list):
        print(f"Error: {MINIDEV_SQLITE_PATH} should be a list of dictionaries.")
        return

    # 3. Combine Ground Truth with Predictions
    # We use a dictionary keyed by question_id to ensure uniqueness.
    # If the script is rerun, it rebuilds this dict from scratch, preventing duplicates.
    combined_results_map = {}

    print("Combining data...")
    matched_count = 0
    missing_count = 0

    for item in minidev_data:
        q_id = str(item.get("question_id")) # Ensure ID is string for lookup
        
        # Check if we have a prediction for this question
        if q_id in all_predictions:
            # Create a copy of the ground truth item to avoid mutating original
            new_entry = item.copy()
            
            # Extract and clean the predicted SQL
            raw_pred = all_predictions[q_id]
            clean_sql = clean_prediction_sql(raw_pred)
            
            # Add the prediction to the entry
            # You can rename "predicted_sql" to whatever your downstream evaluation needs
            new_entry["predicted_sql"] = clean_sql
            
            # Add to our map (Keying by ID ensures NO DUPLICATES in output)
            combined_results_map[q_id] = new_entry
            matched_count += 1
        else:
            missing_count += 1

    # Convert the unique map back to a list
    final_output_list = list(combined_results_map.values())

    # 4. Save Final Output
    with open(FINAL_COMBINED_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(final_output_list, f, indent=4)

    print("-" * 30)
    print(f"Processing Complete.")
    print(f"Total entries in ground truth: {len(minidev_data)}")
    print(f"Entries matched and saved:     {matched_count}")
    print(f"Entries skipped (no prediction): {missing_count}")
    print(f"Final output saved to: {FINAL_COMBINED_OUTPUT}")

if __name__ == "__main__":
    main()