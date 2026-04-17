import json
import argparse
import os
import sys
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
import datetime

# ================= CONFIGURATION =================
DEFAULT_MODEL = "gpt-5-mini" 
TRUNCATION_THRESHOLD = 30  # If rows exceed this, we truncate
HEAD_TAIL_COUNT = 5        # How many rows to keep at start/end
# =================================================

client = OpenAI()

def truncate_output(output_obj, threshold=TRUNCATION_THRESHOLD, keep=HEAD_TAIL_COUNT):
    """
    Returns (summary_text, was_truncated_bool)
    """
    was_truncated = False
    if not output_obj:
        return "No Output / Execution Failed", False
    
    rows = []
    cols = []
    
    if isinstance(output_obj, list):
        rows = output_obj
        cols = ["(Unknown Columns)"]
    elif isinstance(output_obj, dict):
        rows = output_obj.get("rows", [])
        cols = output_obj.get("columns", [])
    else:
        return str(output_obj)[:500], False

    row_count = len(rows)
    summary = f"Columns: {cols}\n"
    summary += f"Total Rows: {row_count}\n"
    summary += "-" * 20 + "\n"

    if row_count <= threshold:
        for r in rows:
            summary += str(r) + "\n"
    else:
        was_truncated = True
        head = rows[:keep]
        tail = rows[-keep:]
        for r in head:
            summary += str(r) + "\n"
        skipped = row_count - (keep * 2)
        summary += f"\n... [ {skipped} rows omitted for brevity ] ...\n\n"
        for r in tail:
            summary += str(r) + "\n"

    return summary, was_truncated

def construct_prompt(item):
    q_id = item.get("question_id")
    question = item.get("question")
    db_id = item.get("db_id")
    
    gold_sql = item.get("gold_sql") or item.get("sql")
    # Get text and truncation status
    gold_out, gold_trunc = truncate_output(item.get("gold_sql_output") or item.get("sqloutput"))
    pred_sql_out, sql_trunc = truncate_output(item.get("predicted_sql_output"))
    pred_sparql_out, sparql_trunc = truncate_output(item.get("sparqloutput"))

    pred_sql = item.get("predicted_sql", "NO_PREDICTION")
    pred_sparql = item.get("sparql", "NO_PREDICTION")

    # Add a global warning if truncation happened anywhere
    truncation_note = ""
    if any([gold_trunc, sql_trunc, sparql_trunc]):
        truncation_note = (
            "\nNOTE: Some outputs have been TRUNCATED because they were too large. "
            "The 'Total Rows' count is accurate. Do not penalize a query for 'missing rows' "
            "if the total row counts match, even if the middle rows are hidden in this prompt.\n"
        )

    system_message = f"""You are an expert Database QA Judge. Your task is to evaluate two predicted queries (SQL and SPARQL) against a Gold Standard SQL query. You must judge semantic correctness, NOT syntactic or formatting similarity.{truncation_note}"""

    system_message += """
    
    Evaluation Criteria:
    1. Ignore column names and output formatting.
    2. Focus only on semantic equivalence of the values and row counts.
    3. Allow small numeric rounding differences.
    4. Extra columns in the SPARQL output are allowed if the correct answer is present.
    5. Treat rows as unordered sets if no ordering is required by the question.

    Output strictly in JSON format ONLY as follows:
    {
      "sql_eval": {
        "reasoning": "Step-by-step analysis of why the SQL is correct or incorrect.",
        "status": "CORRECT" | "WRONG_ANSWER" | "EXECUTION_ERROR"
      },
      "sparql_eval": {
        "reasoning": "Step-by-step analysis. If results are empty, check if it's a Schema Mismatch (wrong predicates) vs Logic Error.",
        "status": "CORRECT" | "WRONG_ANSWER" | "EXECUTION_ERROR" | "SCHEMA_MISMATCH",
        "error_category": "NONE" | "SYNTAX" | "SCHEMA" | "LOGIC" | "HALLUCINATION"
      },
      "comparison": {
        "summary": "One sentence summary.",
        "winner": "SQL" | "SPARQL" | "TIE_BOTH_CORRECT" | "TIE_BOTH_INCORRECT"
      }
    }"""

    user_message = f"""
    DB Context: {db_id}
    Question: {question}

    --- GROUND TRUTH ---
    Gold SQL: {gold_sql}
    Output:
    {gold_out}

    --- PRED A (SQL) ---
    Query: {pred_sql}
    Output:
    {pred_sql_out}

    --- PRED B (SPARQL) ---
    Query: {pred_sparql}
    Output:
    {pred_sparql_out}
    """
    
    return system_message, user_message

def call_llm_judge(item, model):
    system_msg, user_msg = construct_prompt(item)
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ]
    
    try:
        kwargs = {
                    "model": model,
                    "messages": messages,
                    "response_format": {"type": "json_object"}
                }
        
        # Add reasoning effort if using GPT-5
        if "gpt-5" in model:
            kwargs["reasoning_effort"] = "low"
        else:
            kwargs["temperature"] = 0.0

        response = client.chat.completions.create(**kwargs)
        
        eval_json = json.loads(response.choices[0].message.content)
        
        full_interaction_log = {
            "request": kwargs, # Log exactly what was sent
            "response": response.model_dump(),
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return eval_json, full_interaction_log
        
    except Exception as e:
        # Maintain consistent structure even on failure
        error_log = {
            "error": str(e),
            "request": {"model": model, "messages": messages},
            "timestamp": datetime.datetime.now().isoformat()
        }
        return None, error_log
        
def main():
    parser = argparse.ArgumentParser(description="LLM Judge for SQL vs SPARQL comparison.")
    parser.add_argument("--input_file", type=str, help="Path to final_full_results.json")
    parser.add_argument("--exp_id", type=str, required=True, help="Experiment ID for output folder separation")
    parser.add_argument("--db_id", type=str, default=None, help="Filter by specific DB ID")
    parser.add_argument("--q_ids", type=str, default=None, help="Filter by specific QIDs (comma separated)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Model to use (default: gpt-4.1-mini)")
    parser.add_argument("--max_samples", type=int, default=None, help="Limit number of samples for testing")

    args = parser.parse_args()

    # Setup Paths
    base_results_dir = Path("experiments/bird_minidev/results/10/judge_results") / args.exp_id
    base_results_dir.mkdir(parents=True, exist_ok=True)
    
    input_file = Path("experiments/bird_minidev/results/10/f1_all_scores.json")
    output_eval_file = base_results_dir / "judge_1_evaluation_results.json"
    output_log_file = base_results_dir / "judge_1_execution_logs.json"

    # Load Data
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        sys.exit(1)
        
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filtering Logic
    target_qids = set()
    if args.q_ids:
        target_qids = set(args.q_ids.split(","))

    queue = []
    for item in data:
        qid_str = str(item.get("question_id"))
        
        # Filter by DB
        if args.db_id and item.get("db_id") != args.db_id:
            continue
        
        # Filter by QID
        if target_qids and qid_str not in target_qids:
            continue
            
        queue.append(item)

    # Limit samples if requested
    if args.max_samples:
        queue = queue[:args.max_samples]

    print(f"Starting Evaluation on {len(queue)} items using {args.model}...")
    print(f"Outputs will be saved to: {base_results_dir}")

    eval_results = []
    full_logs = []

    # Processing Loop
    for item in tqdm(queue, desc="Judging"):
        qid = item.get("question_id")
        
        # Call LLM
        eval_json, full_log = call_llm_judge(item, args.model)
        
        if eval_json:
            result_entry = {
                "question_id": qid,
                "db_id": item.get("db_id"),
                "question": item.get("question"),
                "difficulty": item.get("difficulty"),
                "judge_evaluation": eval_json
            }
            eval_results.append(result_entry)
            
            log_entry = {
                "question_id": qid,
                "api_response": full_log
            }
            full_logs.append(log_entry)

    # Save Files
    print(f"Saving {len(eval_results)} evaluations...")
    with open(output_eval_file, 'w', encoding='utf-8') as f:
        json.dump(eval_results, f, indent=4)
        
    print(f"Saving full logs (for cost calc)...")
    with open(output_log_file, 'w', encoding='utf-8') as f:
        json.dump(full_logs, f, indent=4)

    print("Evaluation Complete.")

if __name__ == "__main__":
    main()