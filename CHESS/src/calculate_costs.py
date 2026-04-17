import os
import re
from glob import glob

# -----------------------------------------------------------------------------
# USER CONFIGURATION
# -----------------------------------------------------------------------------
# Add your folders or specific files here. 
# You can mix and match folders and files.
INPUT_PATHS = [
        # "results/dev/CHESS_IR_CG_UT/mini_dev_sqlite/2026-01-25T17:21:19.357167/logs", 
        # "results/dev/CHESS_IR_CG_UT/remaining_minidev/2026-01-25T23:01:02.705158/logs",
        # "results/dev/CHESS_IR_CG_UT/remaining_minidev/2026-01-26T17:20:22.573920/logs",

        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T11:43:19.194613/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T12:05:45.226230/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T14:32:57.845402/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T14:40:39.015609/logs",
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T15:07:33.523260/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T15:24:26.748275/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T15:29:01.641260/logs",
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T16:07:41.630648/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T17:07:35.365769/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T18:39:02.423348/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T19:08:09.779057/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T19:38:35.609799/logs", 
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T20:16:18.510128/logs",
		# "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T14:09:32.681899/logs",
		# "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T14:32:08.661216/logs",
		# "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T16:21:48.320997/logs",
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T16:54:12.738394/logs",
		# "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T17:07:42.829216/logs", 
		# "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T17:26:11.828688/logs", 
		# "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T17:46:49.531420/logs",
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T17:57:19.844700/logs"

        # without evidence runs:
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-01T23:30:27.252809/logs"

        # reasoning_effort=low runs:
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-01T23:43:36.957090/logs" #1472 correct

        # reasoning_effort=minimal runs:
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-01T23:50:37.861331/logs"
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-01T23:56:21.425347/logs"

        # 4.1 mini runs:
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:05:25.110523/logs"

        # all 5-mini engines with reasoning_effort=minimal:
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:12:59.726863/logs" # challenging  1476 incorrect 0.04$
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:16:21.955136/logs" # moderate 1479 incorrect 0.05
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:29:43.936747/logs" # all 5-mini but with reasoning_effort=low 1472 correct 0.0391
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:31:17.926923/logs" # all 5-mini but with reasoning_effort=minimal 1472 correct 0.0511

        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-07T23:25:32.726328/logs" # 358 correct even with unexpected keyword argument 'model_kwargs' error
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:01:27.347408/logs" # 469 updated code; default(minimal on engine configs) on cg, else low
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:04:42.085556/logs" # 368 engine_configs minimal
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:09:28.238758/logs" # 368 removed model_kwargs arg from function call 0.0390$ still correct
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:18:38.816311/logs" # 368 removed model_kwargs from yaml too
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:23:57.621501/logs"
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:32:00.176132/logs"
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:39:34.770011/logs"

        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T12:06:41.709586/logs"
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T12:34:46.941227/logs"

        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T13:01:27.526691/logs"
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T13:22:34.581056/logs"
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T13:37:16.561357/logs"

        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-01T23:30:27.252809/logs", #1471
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-01T23:43:36.957090/logs", #1472
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:05:25.110523/logs", #1473
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:12:59.726863/logs", #1476
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-02T00:16:21.955136/logs", #1479
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-07T23:25:32.726328/logs", #358
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:01:27.347408/logs", #469
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:04:42.085556/logs", #368
        # # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:09:28.238758/logs", #368
        # # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:18:38.816311/logs", #368
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:23:57.621501/logs", #383
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-08T00:39:34.770011/logs", #466
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T12:06:41.709586/logs", #468
        # # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T12:34:46.941227/logs", #472, 473
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T13:22:34.581056/logs", #472, 473
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-03-15T13:37:16.561357/logs", # 347, 349, 352, 291, 397, 402

        # april 6, without evidence runs:
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T14:37:07.202685/logs", # 750
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T14:56:30.771076/logs",

        # same as last one but independently for 5 ques out of them
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T14:56:30.771076/logs/1031_european_football_2.log",
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T14:56:30.771076/logs/1239_thrombosis_prediction.log",
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T14:56:30.771076/logs/1457_student_club.log",
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T14:56:30.771076/logs/486_card_games.log",
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T14:56:30.771076/logs/801_superhero.log"

        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T18:06:23.734829/logs"

        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-06T18:56:22.198034/logs" # 20 ques from only sql correct
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T17:53:13.042141/logs" # next 20 ques from only sql correct
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T18:48:19.582508/logs" # next 20 ques from only sql correct
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T21:00:18.231243/logs" # next 20 ques from only sql correct
        # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T22:13:58.173967/logs"
        "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-04-08T22:59:13.319371/logs" # last 20 ques from only sql correct

    # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-01-30T17:07:35.365769/logs",
    # "results/dev/CHESS_IR_SS_CG/remaining_minidev/2026-02-10T17:57:19.844700/logs"
    # "results/another_run/logs/",
    # "specific_file.log"
]

# -----------------------------------------------------------------------------
# PRICING CONSTANTS (Per 1 Million Tokens)
# Based on: https://platform.openai.com/docs/models/gpt-5-mini
# -----------------------------------------------------------------------------
MODEL_NAME = "gpt-5-mini"
PRICE_INPUT_PER_1M  = 0.25   # $0.25 per 1M input tokens
PRICE_OUTPUT_PER_1M = 2.00   # $2.00 per 1M output tokens

# MODEL_NAME = "gpt-4.1-mini"
# PRICE_INPUT_PER_1M  = 0.40   # 0.15$ more expensive than gpt-5-mini
# PRICE_OUTPUT_PER_1M = 1.60   # 0.4$ cheaper than gpt-5-mini

# Regex to capture your specific log format:
# [Step 1] TOKEN USAGE: Input=450 | Output=120 | Total=570
# 1. Updated Regex to capture the new Reasoning group
# Capture groups: 1=Input, 2=Output, 3=Reasoning, 4=Total
LOG_PATTERN = re.compile(r"\[Step.*?Input=(\d+).*?Output=(\d+)\s*\(Reasoning=(\d+)\).*?Total=(\d+)")

def calculate_file_cost(file_path):
    """Parses a single log file and returns token counts and cost."""
    total_input = 0
    total_output = 0
    total_reasoning = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = LOG_PATTERN.search(line)
                if match:
                    inp = int(match.group(1))
                    out = int(match.group(2))
                    reas = int(match.group(3))
                    
                    total_input += inp
                    total_output += out
                    total_reasoning += reas
                    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    # Calculate Cost
    # Note: total_output ALREADY includes total_reasoning per OpenAI's API metadata structure.
    # We log reasoning separately just for visibility.
    cost_input = (total_input / 1_000_000) * PRICE_INPUT_PER_1M
    cost_output = (total_output / 1_000_000) * PRICE_OUTPUT_PER_1M
    total_cost = cost_input + cost_output

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "reasoning_tokens": total_reasoning, # New tracked metric
        "total_tokens": total_input + total_output,
        "total_cost": total_cost
    }
    
def scan_paths(paths):
    """Scans a list of paths (files or directories) and prints a cost report."""
    
    files_to_process = set() # Use a set to avoid duplicates if paths overlap
    
    print(f"Scanning {len(paths)} input path(s)...")

    for path in paths:
        path = path.strip() # Clean whitespace
        if not path: continue

        if os.path.isfile(path):
            files_to_process.add(os.path.abspath(path))
        elif os.path.isdir(path):
            # Recursive search for .txt, .log, and .json files
            for ext in ["*.txt", "*.log", "*.json"]:
                found = glob(os.path.join(path, "**", ext), recursive=True)
                for f in found:
                    files_to_process.add(os.path.abspath(f))
        else:
            # Try treating it as a glob pattern directly (e.g. "logs/*.log")
            found = glob(path)
            if found:
                for f in found:
                    if os.path.isfile(f):
                        files_to_process.add(os.path.abspath(f))
            else:
                print(f"Warning: Path not found or empty: {path}")

    if not files_to_process:
        print("No valid log files found in the provided paths.")
        return

    print(f"{'='*105}")
    print(f" COST REPORT FOR MODEL: {MODEL_NAME}")
    print(f" Rates: ${PRICE_INPUT_PER_1M}/1M Input | ${PRICE_OUTPUT_PER_1M}/1M Output")
    print(f"{'='*105}")
    print(f"{'File Name':<40} | {'Input':<8} | {'Output (Reas)':<15} | {'Total':<10} | {'Cost ($)'}")
    print(f"{'-'*105}")

    grand_total_tokens = 0
    grand_total_cost = 0.0
    files_with_data = 0

    # Sort files for cleaner output
    for file_path in sorted(list(files_to_process)):
        stats = calculate_file_cost(file_path)
        
        # Only print if tokens were found
        if stats and stats['total_tokens'] > 0:
            file_name = os.path.basename(file_path)
            # Truncate filename if too long for the table
            if len(file_name) > 48:
                file_name = file_name[:45] + "..."
            
            out_str = f"{stats['output_tokens']} ({stats['reasoning_tokens']})"
            print(f"{file_name:<40} | {stats['input_tokens']:<8} | {out_str:<15} | {stats['total_tokens']:<10} | ${stats['total_cost']:.5f}")
            
            grand_total_tokens += stats['total_tokens']
            grand_total_cost += stats['total_cost']
            files_with_data += 1

    print(f"{'='*105}")
    print(f"SUMMARY")
    print(f"Files Processed (with data): {files_with_data} / {len(files_to_process)}")
    print(f"Total Tokens:                {grand_total_tokens:,}")
    print(f"TOTAL COST:                  ${grand_total_cost:.4f}")
    print(f"{'='*105}")

if __name__ == "__main__":
    scan_paths(INPUT_PATHS)