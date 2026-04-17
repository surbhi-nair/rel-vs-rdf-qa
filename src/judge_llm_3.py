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
    question = item.get("question")
    db_id = item.get("db_id")
    
    # Get text and truncation status
    pred_sql_out, sql_trunc = truncate_output(item.get("predicted_sql_output"))
    pred_sparql_out, sparql_trunc = truncate_output(item.get("sparqloutput"))

    truncation_note = ""
    if any([sql_trunc, sparql_trunc]):
        truncation_note = (
            "\nNOTE: Some outputs have been TRUNCATED because they were too large. "
            "Compare based on 'Total Rows' and visible sample data.\n"
        )

    system_message = f"""You are a User Experience Researcher specializing in Data Systems and Question Answering Agents. 
    You are comparing two agents: Agent A and Agent B. 
    You do NOT have a ground truth. You must evaluate which agent provides a more helpful, plausible, and high-quality response to the user's natural language question, prioritizing factual alignment, data integrity, and human-centric clarity.{truncation_note}"""

    system_message += """
    Evaluation Criteria:
    1. CONSISTENCY: Do the two agents agree on the answer? (Same row counts and values).
    2. PLAUSIBILITY: Does the data returned logically answer the question? (e.g., if the user asks for 'Total Salary', a result of negative values or a list of names without a total is a failure).
    3. UTILITY: Which output is easier for a human to read and use immediately?
    4. CONFIDENCE: Based on the data distribution, which agent feels more 'correct' (e.g., one agent returns 50 valid rows, the other returns 0).
    5. PERCEIVED WINNER: Based on the above, select the agent that provided the most accurate, complete, and human-usable data, or declare a TIE if both results are functionally identical or equally flawed.

    Output strictly in JSON format ONLY as follows:
    {
      "evaluation": {
        "consensus_status": "FULL_AGREEMENT" | "PARTIAL_AGREEMENT" | "TOTAL_DISAGREEMENT",
        "plausibility_check": "Brief analysis of whether the results 'make sense' for the question asked.",
        "utility_comparison": "Brief comparison of the formatting, column clarity, and readability of A vs B for a human user.",
        "perceived_winner": "AGENT_A" | "AGENT_B" | "TIE",
        "winning_reason": "Specific reason why the winner was chosen (or why it's a tie).",
        "confidence_score": 1-10
      }
    }"""

    user_message = f"""
    USER QUESTION: {question}
    DATABASE CONTEXT: {db_id}

    --- AGENT A RESULT ---
    {pred_sql_out}

    --- AGENT B RESULT ---
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
        
        if "gpt-5" in model:
            kwargs["reasoning_effort"] = "low"
        else:
            kwargs["temperature"] = 0.0

        response = client.chat.completions.create(**kwargs)
        eval_json = json.loads(response.choices[0].message.content)
        
        full_interaction_log = {
            "request": kwargs,
            "response": response.model_dump(),
            "timestamp": datetime.datetime.now().isoformat()
        }
        return eval_json, full_interaction_log
        
    except Exception as e:
        return None, {"error": str(e), "timestamp": datetime.datetime.now().isoformat()}

def main():
    parser = argparse.ArgumentParser(description="LLM Judge with checkpointing.")
    parser.add_argument("--exp_id", type=str, required=True)
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL)
    parser.add_argument("--max_samples", type=int, default=None)
    args = parser.parse_args()

    # Paths
    base_results_dir = Path("experiments/bird_minidev/results/8/judge_results") / args.exp_id
    base_results_dir.mkdir(parents=True, exist_ok=True)
    
    input_file = Path("experiments/bird_minidev/results/8/f1_all_scores.json")
    output_eval_file = base_results_dir / "judge_3_evaluation_results.json"
    output_log_file = base_results_dir / "judge_3_execution_logs.json"

    # 1. Load existing results to support resuming
    eval_results = []
    full_logs = []
    processed_qids = set()

    if output_eval_file.exists():
        with open(output_eval_file, 'r', encoding='utf-8') as f:
            eval_results = json.load(f)
            processed_qids = {str(item["question_id"]) for item in eval_results}
            print(f"Resuming: Found {len(processed_qids)} already processed questions.")

    if output_log_file.exists():
        with open(output_log_file, 'r', encoding='utf-8') as f:
            full_logs = json.load(f)

    # 2. Load Input Data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 3. Filter Queue (Remove already processed)
    queue = []
    for item in data:
        qid_str = str(item.get("question_id"))
        if qid_str in processed_qids:
            continue
        queue.append(item)

    if args.max_samples:
        queue = queue[:args.max_samples]

    if not queue:
        print("No new questions to process.")
        return

    print(f"Processing {len(queue)} new items...")

    # 4. Processing Loop with Atomic Saving
    for item in tqdm(queue, desc="Judging"):
        qid = item.get("question_id")
        eval_json, full_log = call_llm_judge(item, args.model)
        
        if eval_json:
            # Append to memory
            eval_results.append({
                "question_id": qid,
                "db_id": item.get("db_id"),
                "question": item.get("question"),
                "difficulty": item.get("difficulty"),
                "judge_evaluation": eval_json
            })
            full_logs.append({
                "question_id": qid,
                "api_response": full_log
            })

            # Save immediately to disk (Atomic update)
            with open(output_eval_file, 'w', encoding='utf-8') as f:
                json.dump(eval_results, f, indent=4)
            with open(output_log_file, 'w', encoding='utf-8') as f:
                json.dump(full_logs, f, indent=4)

    print(f"Evaluation Complete. Total records in file: {len(eval_results)}")

if __name__ == "__main__":
    main()