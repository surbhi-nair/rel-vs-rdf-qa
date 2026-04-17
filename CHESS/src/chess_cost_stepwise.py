import os
import re
from glob import glob

INPUT_PATHS = [
    "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T18:06:23.734829/logs", # 5 ques, no evidence, 4.1 mini for all steps except gen/revise which are gpt-5-mini
]

# --- PRICING CONFIGURATION ---
# Format: "step_name": ("model_name", input_price_per_1M, output_price_per_1M)
STEP_MODEL_MAP = {
    "extract_keywords":   ("gpt-4.1-mini", 0.40, 1.60),
    "filter_column":      ("gpt-4.1-mini", 0.40, 1.60),
    "select_tables":      ("gpt-4.1-mini", 0.40, 1.60),
    "select_columns":     ("gpt-4.1-mini", 0.40, 1.60),
    "generate_candidate_one": ("gpt-5-mini", 0.25, 2.00),
    "revise_one":         ("gpt-5-mini", 0.25, 2.00),
    "DEFAULT":            ("gpt-5-mini", 0.25, 2.00) 
}

# Updated Regex:
# Group 1: Step Name
# Group 2: Input Tokens
# Group 3: Output Tokens
# Group 4: Reasoning Tokens
# Group 5: Total Tokens
LOG_PATTERN = re.compile(r"\[Step\s+(.*?)\]\s+TOKEN USAGE:\s+Input=(\d+).*?Output=(\d+)\s*\(Reasoning=(\d+)\).*?Total=(\d+)")

def calculate_file_cost(file_path):
    """Parses a single log file and returns token counts and cost per model."""
    total_input = 0
    total_output = 0
    total_reasoning = 0
    total_cost = 0.0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = LOG_PATTERN.search(line)
                if match:
                    step_name = match.group(1).strip().lower()
                    inp = int(match.group(2))
                    out = int(match.group(3))
                    reas = int(match.group(4))
                    
                    # Determine which pricing to use
                    model_info = STEP_MODEL_MAP.get(step_name, STEP_MODEL_MAP["DEFAULT"])
                    model_name, price_in, price_out = model_info
                    
                    # Calculate cost for this specific line/step
                    line_cost = ((inp / 1_000_000) * price_in) + ((out / 1_000_000) * price_out)
                    
                    total_input += inp
                    total_output += out
                    total_reasoning += reas
                    total_cost += line_cost
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "reasoning_tokens": total_reasoning,
        "total_tokens": total_input + total_output,
        "total_cost": total_cost
    }
    
def scan_paths(paths):
    files_to_process = set()
    print(f"Scanning {len(paths)} input path(s)...")

    for path in paths:
        path = path.strip()
        if not path: continue
        if os.path.isfile(path):
            files_to_process.add(os.path.abspath(path))
        elif os.path.isdir(path):
            for ext in ["*.txt", "*.log", "*.json"]:
                found = glob(os.path.join(path, "**", ext), recursive=True)
                for f in found:
                    files_to_process.add(os.path.abspath(f))
        else:
            found = glob(path)
            if found:
                for f in found:
                    if os.path.isfile(f):
                        files_to_process.add(os.path.abspath(f))

    if not files_to_process:
        print("No valid log files found.")
        return

    print(f"{'='*105}")
    print(f" COST REPORT (Multi-Model per Step)")
    print(f"{'='*105}")
    print(f"{'File Name':<40} | {'Input':<8} | {'Output (Reas)':<15} | {'Total':<10} | {'Cost ($)'}")
    print(f"{'-'*105}")

    grand_total_tokens = 0
    grand_total_cost = 0.0
    files_with_data = 0

    for file_path in sorted(list(files_to_process)):
        stats = calculate_file_cost(file_path)
        
        if stats and stats['total_tokens'] > 0:
            file_name = os.path.basename(file_path)
            if len(file_name) > 40:
                file_name = file_name[:37] + "..."
            
            out_str = f"{stats['output_tokens']} ({stats['reasoning_tokens']})"
            print(f"{file_name:<40} | {stats['input_tokens']:<8} | {out_str:<15} | {stats['total_tokens']:<10} | ${stats['total_cost']:.5f}")
            
            grand_total_tokens += stats['total_tokens']
            grand_total_cost += stats['total_cost']
            files_with_data += 1

    print(f"{'='*105}")
    print(f"SUMMARY")
    print(f"Files Processed (with data): {files_with_data} / {len(files_to_process)}")
    print(f"Total Tokens:                {grand_total_tokens:,}")
    print(f"TOTAL COST (Mixed Models):   ${grand_total_cost:.4f}")
    print(f"{'='*105}")

if __name__ == "__main__":
    scan_paths(INPUT_PATHS)