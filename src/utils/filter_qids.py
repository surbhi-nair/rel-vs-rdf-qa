import json

data = json.load(open('experiments/bird_minidev/results/8/judge_results/judgec_results.json'))

def get_ids_by_condition(entities):
    sql_only_correct = []
    sparql_only_correct = []

    for item in entities:
        qid = str(item["question_id"])
        evals = item.get("judge_evaluation", {})
        
        sql_status = evals.get("sql_eval", {}).get("status")
        sparql_status = evals.get("sparql_eval", {}).get("status")

        # Condition 1: SQL is CORRECT and SPARQL is NOT CORRECT
        if sql_status == "CORRECT" and sparql_status != "CORRECT":
            sql_only_correct.append(qid)
        
        # Condition 2: SPARQL is CORRECT and SQL is NOT CORRECT
        elif sparql_status == "CORRECT" and sql_status != "CORRECT":
            sparql_only_correct.append(qid)

    print(f"SQL Correct only: {','.join(sql_only_correct)}, Total: {len(sql_only_correct)}")
    print()
    print(f"SPARQL Correct only: {','.join(sparql_only_correct)}, Total: {len(sparql_only_correct)}")

# Run the function
get_ids_by_condition(data)