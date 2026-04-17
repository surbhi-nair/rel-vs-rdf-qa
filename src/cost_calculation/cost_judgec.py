import json
from pathlib import Path

# ================= 2026 PRICING CONFIGURATION =================
PRICING = {
    "gpt-4.1-mini": {
        "input_standard": 0.40,
        "input_cached":   0.20,
        "output":         1.60
    },
    "gpt-5-mini": {
        "input_standard": 0.25,
        "input_cached":   0.025,
        "output":         2.00
    }
}

# Add your list of log files here
LOG_FILES = [
    # "experiments/bird_minidev/results/8/judge_results/1/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/2/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/3/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/4/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/5/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/6/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/7/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/8/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/9/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/10/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/11/judge_execution_logs.json"

    # "experiments/bird_minidev/results/8/judge_results/12/judge_execution_logs.json",
    # "experiments/bird_minidev/results/8/judge_results/13/judge_2_execution_logs.json",

    # "experiments/bird_minidev/results/8/judge_results/13/judge_3_execution_logs.json",

    "experiments/bird_minidev/results/10/judge_results/2/judge_1_execution_logs.json",
]
# ==============================================================

def process_all_logs(file_list):
    # Overall accumulators
    grand_metrics = {
        "standard_input": 0,
        "cached_input": 0,
        "visible_output": 0,
        "reasoning_output": 0,
        "total_cost": 0.0
    }
    processed_count = 0
    model_breakdown = {}

    for log_file in file_list:
        file_path = Path(log_file)
        if not file_path.exists():
            print(f"Skipping: File not found -> {log_file}")
            continue

        with open(file_path, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                print(f"Skipping: Invalid JSON in -> {log_file}")
                continue

        processed_count += 1
        
        for entry in logs:
            interaction = entry.get("api_response", {})
            if "error" in interaction: continue
                
            resp = interaction.get("response", {})
            usage = resp.get("usage", {})
            model_used = resp.get("model", "gpt-5-mini")
            
            rates = next((v for k, v in PRICING.items() if k in model_used), PRICING["gpt-5-mini"])

            # 1. Inputs
            prompt_details = usage.get("prompt_tokens_details", {})
            cached = prompt_details.get("cached_tokens", 0)
            std_input = usage.get("prompt_tokens", 0) - cached
            
            # 2. Outputs
            comp_details = usage.get("completion_tokens_details", {})
            reasoning = comp_details.get("reasoning_tokens", 0)
            total_output = usage.get("completion_tokens", 0)
            visible_output = total_output - reasoning

            # 3. Calculate Cost
            call_cost = (std_input * rates["input_standard"] / 1_000_000) + \
                        (cached * rates["input_cached"] / 1_000_000) + \
                        (total_output * rates["output"] / 1_000_000)

            # Update Grand Totals
            grand_metrics["standard_input"] += std_input
            grand_metrics["cached_input"] += cached
            grand_metrics["visible_output"] += visible_output
            grand_metrics["reasoning_output"] += reasoning
            grand_metrics["total_cost"] += call_cost
            
            if model_used not in model_breakdown:
                model_breakdown[model_used] = {"calls": 0, "cost": 0.0}
            model_breakdown[model_used]["calls"] += 1
            model_breakdown[model_used]["cost"] += call_cost

    # Final Consolidated Report
    print(f"\n{'='*55}")
    print(f"            FINAL CONSOLIDATED COST ANALYSIS")
    print(f"{'='*55}")
    print(f"Files Processed:        {processed_count}")
    print(f"Standard Input Tokens:  {grand_metrics['standard_input']:,}")
    print(f"Cached Input Tokens:    {grand_metrics['cached_input']:,}")
    print(f"Visible Output Tokens:  {grand_metrics['visible_output']:,}")
    print(f"Reasoning Tokens:       {grand_metrics['reasoning_output']:,}")
    print(f"{'-'*55}")
    
    for model, stats in model_breakdown.items():
        print(f"Model {model:15}: {stats['calls']:4} calls | Cost: ${stats['cost']:.4f}")
    
    print(f"{'-'*55}")
    print(f"GRAND TOTAL COST:       ${grand_metrics['total_cost']:.4f}")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    process_all_logs(LOG_FILES)