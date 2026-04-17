import json
import argparse
import os
from typing import Dict, Any, List
from openai import OpenAI

# Configuration
MODEL_NAME = "gpt-5-mini"   # or gpt-4.1-mini if needed
MAX_ROW_COUNT = 1550  # Skip LLM evaluation if row count exceeds this to avoid context length errors
client = OpenAI()

# Prompt Template
SYSTEM_PROMPT = """\
You are an expert Data Evaluation Judge.

Your task is to evaluate the performance of a Text-to-SPARQL agent by comparing
its predicted output against a Gold Standard (SQL ground truth).

You must judge semantic correctness, NOT syntactic or formatting similarity.
"""

USER_PROMPT_TEMPLATE = """\
You are given the following inputs:

USER QUESTION:
{question}

GOLD STANDARD (SQL):
SQL QUERY:
{gold_sql}

SQL OUTPUT (Ground Truth):
Columns: {gold_columns}
Rows: {gold_rows}

PREDICTED (SPARQL):
SPARQL QUERY:
{sparql_query}

SPARQL OUTPUT:
Columns: {sparql_columns}
Rows: {sparql_rows}

EVALUATION RULES:
1. Ignore column names and output formatting.
2. Focus only on semantic equivalence of the values.
3. Allow small numeric rounding differences.
4. Extra columns in the SPARQL output are allowed if the correct answer is present.
5. Treat rows as unordered sets if no ordering is required by the question.


OUTPUT FORMAT:
Return ONLY a valid JSON object with these keys:
- "is_correct": true or false
- "reasoning": one concise sentence explaining your decision(if false, explain clearly what is missing/incorrect in the logic of the sparql query compared to the gold sql query)
"""

# LLM Call
def judge_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call LLM to judge semantic equivalence between gold SQL output and SPARQL output.
    """

    # Check if required fields exist and are not None
    if entry.get("sparqloutput") is None:
        response_dict = {
            "id": None,
            "created_at": None,
            "model": MODEL_NAME,
            "status": "skipped",
            "incomplete_details": {
                "reason": "sparqloutput is None"
            },
            "usage": None,
            "output_text": "",
        }
        judgment = {
            "is_correct": False,
            "reasoning": "SPARQL output is missing or None."
        }
        return {"judgment": judgment, "full_response_text": "", "full_response": response_dict}

    if entry.get("sqloutput") is None:
        response_dict = {
            "id": None,
            "created_at": None,
            "model": MODEL_NAME,
            "status": "skipped",
            "incomplete_details": {
                "reason": "sqloutput is None"
            },
            "usage": None,
            "output_text": "",
        }
        judgment = {
            "is_correct": False,
            "reasoning": "SQL output is missing or None."
        }
        return {"judgment": judgment, "full_response_text": "", "full_response": response_dict}

    # Check row counts to avoid context length errors
    sql_row_count = entry.get("sqloutput", {}).get("row_count", 0)
    sparql_row_count = entry.get("sparqloutput", {}).get("row_count", 0)
    
    if sql_row_count > MAX_ROW_COUNT or sparql_row_count > MAX_ROW_COUNT:
        response_dict = {
            "id": None,
            "created_at": None,
            "model": MODEL_NAME,
            "status": "skipped",
            "incomplete_details": {
                "reason": f"row_count exceeds MAX_ROW_COUNT ({MAX_ROW_COUNT}): sql={sql_row_count}, sparql={sparql_row_count}"
            },
            "usage": None,
            "output_text": "",
        }
        judgment = {
            "is_correct": False,
            "reasoning": f"Row count exceeds maximum allowed ({MAX_ROW_COUNT}) to avoid context length errors: SQL row_count={sql_row_count}, SPARQL row_count={sparql_row_count}."
        }
        return {"judgment": judgment, "full_response_text": "", "full_response": response_dict}

    user_prompt = USER_PROMPT_TEMPLATE.format(
        question=entry["question"],
        gold_sql=entry.get("sql", ""),
        gold_columns=entry["sqloutput"]["columns"],
        gold_rows=entry["sqloutput"]["rows"],
        sparql_query=entry.get("sparql", ""),
        sparql_columns=entry["sparqloutput"]["columns"],
        sparql_rows=entry["sparqloutput"]["rows"],
    )

    # response = client.responses.create(
    #     model=MODEL_NAME,
    #     input=[
    #         {"role": "system", "content": SYSTEM_PROMPT},
    #         {"role": "user", "content": user_prompt},
    #     ],
    #     max_output_tokens=300,
    # )
    # try, with simple retry if model was truncated (max_output_tokens)
    max_tokens = 300
    short_fallback = False
    for attempt in range(3):
        response = client.responses.create(
            model=MODEL_NAME,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt + ("\nReturn ONLY the JSON object with the required keys and nothing else." if short_fallback else user_prompt)},
            ],
            max_output_tokens=max_tokens,
        )

        # Debug dump
        # print("Full LLM response object:", repr(response))

        # If not truncated due to token limit, proceed
        inc = getattr(response, "incomplete_details", None)
        if not inc or getattr(inc, "reason", None) != "max_output_tokens":
            break

        # otherwise retry with larger budget and then with JSON-only hint
        # print(f"Response truncated (reason={inc.reason}); retrying with more tokens...")
        max_tokens = max_tokens * 2 if max_tokens < 2000 else 2000
        short_fallback = True

    # print("Full LLM response object:", repr(response))
    # Extract text output
    # text_output = response.output_text.strip()
    # Robust extraction of text from different SDK response shapes
    text_output = ""
    if getattr(response, "output_text", None):
        text_output = response.output_text
    else:
        out = getattr(response, "output", None)
        if out:
            parts = []
            for item in out:
                content = None
                if isinstance(item, dict):
                    content = item.get("content")
                else:
                    content = getattr(item, "content", None)
                if not content:
                    continue
                for c in content:
                    if isinstance(c, str):
                        parts.append(c)
                    elif isinstance(c, dict):
                        parts.append(c.get("text") or c.get("content") or "")
            text_output = "".join(parts)
        else:
            text_output = str(response)

    text_output = (text_output or "").strip()
    # print(f"LLM Output: {repr(text_output)}")
    # print(f"LLM Output: {text_output}")
    try:
        judgment = json.loads(text_output)
    except json.JSONDecodeError:
        judgment = {
            "is_correct": False,
            "reasoning": "Model did not return valid JSON."
        }

    # Convert response object to dict for JSON serialization
    response_dict = {
        "id": response.id,
        "created_at": response.created_at,
        "model": response.model,
        "status": response.status,
        "incomplete_details": {
            "reason": getattr(response.incomplete_details, "reason", None)
        } if response.incomplete_details else None,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.total_tokens,
        } if response.usage else None,
        "output_text": text_output,
    }

    return {"judgment": judgment, "full_response_text": text_output, "full_response": response_dict}

def run_evaluation(input_path: str, output_path: str, full_response_path: str):
    with open(input_path, "r") as f:
        data = json.load(f)

    # Load existing results to skip already processed questions
    results: List[Dict[str, Any]] = []
    full_responses: List[Dict[str, Any]] = []
    processed_question_ids = set()
    
    if os.path.exists(output_path):
        try:
            with open(output_path, "r") as f:
                results = json.load(f)
                processed_question_ids = {result["question_id"] for result in results}
        except Exception:
            results = []
    
    if os.path.exists(full_response_path):
        try:
            with open(full_response_path, "r") as f:
                full_responses = json.load(f)
        except Exception:
            full_responses = []

    for entry in data:
        qid = entry["question_id"]
        if qid in processed_question_ids:
            print(f"Skipping QID {qid} (already processed)...")
            continue
        
        print(f"Evaluating QID {qid}...")
        judge_result = judge_entry(entry)
        judgment = judge_result["judgment"]
        full_response_text = judge_result["full_response_text"]
        full_response = judge_result["full_response"]

        results.append({
            "question_id": qid,
            "db_id": entry["db_id"],
            "judgment": judgment,
        })
        
        full_responses.append({
            "question_id": qid,
            "db_id": entry["db_id"],
            "full_llm_response": full_response,
        })

        # Save results immediately after each entry is processed
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        with open(full_response_path, "w") as f:
            json.dump(full_responses, f, indent=2)

        print(f"Saved results for QID {qid}")

    print(f"\nSemantic evaluation saved to {output_path}")
    print(f"Full LLM responses saved to {full_response_path}")

if __name__ == "__main__":
    input_json = "experiments/bird_minidev/results/judge-llm-test-input.json"
    output_json = "experiments/bird_minidev/results/judge-llm-test-output.json"
    full_llm_responses_json = "experiments/bird_minidev/results/judge-llm-full-responses.json"
    # input_json = "experiments/bird_minidev/results/8/results_executed.json"
    # output_json = "experiments/bird_minidev/results/8/judge-llm-output.json"
    # full_llm_responses_json = "experiments/bird_minidev/results/8/judge-llm-full-responses.json"
    run_evaluation(input_json, output_json, full_llm_responses_json)