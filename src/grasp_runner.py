import json
import requests
import os
import time
import argparse
from pathlib import Path

GRASP_URL = "http://tagus:10001/run"
INPUT_JSON = "data/MINIDEV/mini_dev_sqlite.json"
BASE_OUTPUT_DIR = Path("experiments/bird_minidev/results")
# BASE_OUTPUT_DIR = Path("experiments/bird_minidev_basic/results") # TODO: comment this and uncomment the above line when you want to run on the semantic RML mapping results instead of the simpler ones
USE_EVIDENCE = True  # Set to True to append evidence to the question when sending to GRASP (if evidence exists)

# OUTPUT_JSON = "experiments/bird_minidev/results.json"
# GRASP_OUTPUT_JSON = "experiments/bird_minidev/results_grasp_full.json"

"""Batch-run questions through the GRASP sparql-qa endpoint and save results.
Resumes from existing results.json to avoid re-querying; saves concise and full GRASP outputs.
Usage: python grasp_runner.py [--db_id DB] [--exp_id EXP]
"""
def load_existing_results(output_path):
    """Load already saved results so we don't re-query."""
    if not os.path.exists(output_path):
        return []

    with open(output_path, "r") as f:
        try:
            return json.load(f)
        except:
            return []

def call_grasp(question, db, qid, timeout=100, max_timeout=200):
    """Send question to GRASP and return sparql + result with retry on timeout."""
    payload = {
        "task": "sparql-qa",
        "input": question,
        "knowledge_graphs": [db]
    }

    try:
        response = requests.post(GRASP_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data

    except requests.exceptions.Timeout:
        if timeout < max_timeout:
            print(f"⏳ Timeout for QID {qid}, retrying with longer timeout ({max_timeout}s)…")
            return call_grasp(question, db, qid, timeout=max_timeout, max_timeout=max_timeout)
        else:
            print(f"Timeout exceeded max limit for QID {qid}")
            return {"sparql": None, "result": None}

    except Exception as e:
        print(f"Exception caught for question QID {qid}")
        print(e)
        return {"sparql": None, "result": None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_id",
        type=str,
        default=None,
        help="Filter: only process questions with this db_id"
    )
    parser.add_argument(
        "--exp_id",
        type=str,
        default=None,
        help="Experiment ID: subfolder name under experiments/bird_minidev/results (e.g., '1', 'test'). If not provided, uses base path.",
        required=True
    )
    args = parser.parse_args()

    filter_db_id = args.db_id
    exp_id = args.exp_id
    print(f"Starting GRASP runner with filter_db_id={filter_db_id} and exp_id={exp_id}")

    # Determine output directory
    if exp_id:
        output_dir = BASE_OUTPUT_DIR / exp_id
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = BASE_OUTPUT_DIR

    OUTPUT_JSON = output_dir / "results.json"
    GRASP_OUTPUT_JSON = output_dir / "results_grasp_full.json"

    if filter_db_id:
        print(f"Filtering questions: only db_id = '{filter_db_id}'")

    # Load all questions
    with open(INPUT_JSON, "r") as f:
        questions = json.load(f)

    # Load existing results
    saved_results = load_existing_results(output_path=OUTPUT_JSON)
    saved_results_grasp = load_existing_results(output_path=GRASP_OUTPUT_JSON)
    # Build index by question_id for fast lookup
    saved_by_id = {item.get("question_id"): item for item in saved_results}
    saved_by_id_grasp = {item.get("question_id"): item for item in saved_results_grasp}
    print(f"Resuming… {len(saved_by_id)} questions already done.")

    results = saved_results[:]
    grasp_results = saved_results_grasp[:]

    for item in questions:
        qid = item["question_id"]
        db_id = item["db_id"]

        # Apply db_id filter
        if filter_db_id and db_id != filter_db_id:
            continue

        # logic to skip existing question_id
        if qid in saved_by_id:
            existing = saved_by_id[qid]

            # If result is NOT None → skip
            if existing.get("sparql") is not None:
                print(f"Skipping QID {qid} (already answered)")
                continue

            # If result is None → retry
            print(f"Retrying failed question QID {qid}")

        question = item["question"]
        sql = item["SQL"]
        evidence = item.get("evidence", "")
        # append evidence if it exists and is non-empty
        if evidence and USE_EVIDENCE:
            print(f"Appending evidence to question QID {qid}")
            question = question.strip() + " Context: " + evidence.strip()

        print(f"Running question QID {qid}")

        grasp_resp = call_grasp(question, db_id, qid)
        try:
            out = grasp_resp.get("output", {}) # changed to "args" for updated grasp response format
            if not isinstance(out, dict):
                out = {}
            output = {"sparql": out.get("sparql"), "result": out.get("result")} # changed to "answer" for updated grasp response format
        except Exception as e:
            print(f"Error parsing GRASP response for QID {qid}: {e}")
            output = {"sparql": None, "result": None}

        result_entry = {
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "sql": sql,
            "sparql": output["sparql"],
        }

        grasp_output_entry = {
            "question_id": qid,
            "db_id": db_id,
            "question": question,
            "grasp_response": grasp_resp
        }

        # Update or append
        saved_by_id[qid] = result_entry
        saved_by_id_grasp[qid] = grasp_output_entry

        # Reconstruct results list
        results = list(saved_by_id.values())
        grasp_results = list(saved_by_id_grasp.values())

        # Save
        with open(OUTPUT_JSON, "w") as f:
            json.dump(results, f, indent=4)

        with open(GRASP_OUTPUT_JSON, "w") as f:
            json.dump(grasp_results, f, indent=4)

        print(f"💾 Saved result ({len(results)} total)")
        time.sleep(0.2)

    print("\nAll results saved to results.json")


if __name__ == "__main__":
    main()