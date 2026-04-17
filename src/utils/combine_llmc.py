import json
import os
from pathlib import Path

def combine_judge_results(base_path, output_filename="judgec_results.json"):
    combined_data = []
    base_dir = Path(base_path)
    
    # Iterate through folders 1 to 11
    for i in range(1, 12):
        folder_path = base_dir / str(i)
        file_path = folder_path / "judge_evaluation_results.json"
        
        if file_path.exists():
            print(f"Processing: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle if the file content is a list or a single dictionary
                    if isinstance(data, list):
                        combined_data.extend(data)
                    else:
                        combined_data.append(data)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        else:
            print(f"Warning: File not found at {file_path}")

    # Write the combined results to a new file
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=4)
    
    print(f"\nSuccessfully combined {len(combined_data)} entries into {output_filename}")

# --- Set your path here ---
target_path = "experiments/bird_minidev/results/8/judge_results"
output_file = target_path + "/judgec_results.json"
combine_judge_results(target_path,output_file)