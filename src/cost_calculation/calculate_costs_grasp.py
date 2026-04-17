import json
import argparse
from pathlib import Path

# ================= PRICING CONFIGURATION (Per 1 Million Tokens) =================
# TODO: Update these values to the specific pricing for gpt-5-mini if known.
# Using gpt-4o-mini pricing as a placeholder reference:
PRICE_INPUT_1M = 0.15        # $0.15 per 1M input tokens
PRICE_CACHED_INPUT_1M = 0.075 # $0.075 per 1M cached input tokens (usually 50% of input)
PRICE_OUTPUT_1M = 0.60       # $0.60 per 1M output tokens
# ==============================================================================

def calculate_step_cost(usage):
    """
    Calculates cost for a single LLM call based on usage dict.
    """
    if not usage:
        return 0.0, 0, 0, 0

    total_input = usage.get("input_tokens", 0)
    total_output = usage.get("output_tokens", 0)
    
    # Extract cached tokens safely
    details = usage.get("input_tokens_details", {}) or {}
    cached_input = details.get("cached_tokens", 0)
    
    # Calculate Non-Cached Input (The expensive part)
    non_cached_input = max(0, total_input - cached_input)

    # Calculate Cost
    cost_non_cached = (non_cached_input / 1_000_000) * PRICE_INPUT_1M
    cost_cached = (cached_input / 1_000_000) * PRICE_CACHED_INPUT_1M
    cost_output = (total_output / 1_000_000) * PRICE_OUTPUT_1M

    total_cost = cost_non_cached + cost_cached + cost_output

    return total_cost, non_cached_input, cached_input, total_output

def main():
    parser = argparse.ArgumentParser(description="Calculate LLM costs from Grasp logs.")
    parser.add_argument("--file", type=str, help="Path to the .json log file", default="experiments/bird_minidev/results/10/results_grasp_full.json")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        return

    print(f"Loading {file_path}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # If the file contains a single object, wrap it in a list
    if isinstance(data, dict):
        data = [data]

    grand_total_cost = 0.0
    total_non_cached_in = 0
    total_cached_in = 0
    total_out = 0

    print("-" * 80)
    print(f"{'QID':<8} | {'Steps':<6} | {'Input (New)':<12} | {'Input (Cached)':<14} | {'Output':<10} | {'Cost ($)':<10}")
    print("-" * 80)

    for item in data:
        qid = item.get("question_id", "N/A")
        
        # Access the messages list inside grasp_response
        grasp_response = item.get("grasp_response", {})
        messages = grasp_response.get("messages", [])

        q_cost = 0.0
        q_nc_in = 0
        q_c_in = 0
        q_out = 0
        steps_count = 0

        # Iterate through every message/step in the reasoning chain
        for msg in messages:
            # The usage is hidden inside the 'content' dictionary of the assistant
            content = msg.get("content")
            
            # Check if content is a dict (it is for tool calls/reasoning steps) and has usage
            if isinstance(content, dict) and "usage" in content:
                cost, nc_in, c_in, out = calculate_step_cost(content["usage"])
                
                q_cost += cost
                q_nc_in += nc_in
                q_c_in += c_in
                q_out += out
                steps_count += 1

        # Accumulate Grand Totals
        grand_total_cost += q_cost
        total_non_cached_in += q_nc_in
        total_cached_in += q_c_in
        total_out += q_out

        print(f"{str(qid):<8} | {steps_count:<6} | {q_nc_in:<12} | {q_c_in:<14} | {q_out:<10} | ${q_cost:.6f}")

    print("-" * 80)
    print("GRAND TOTAL SUMMARY")
    print("-" * 80)
    print(f"Total Questions:       {len(data)}")
    print(f"Total Non-Cached Input: {total_non_cached_in:,}")
    print(f"Total Cached Input:     {total_cached_in:,}")
    print(f"Total Output:           {total_out:,}")
    print(f"Total Estimated Cost:   ${grand_total_cost:.6f}")
    print("=" * 80)

if __name__ == "__main__":
    main()