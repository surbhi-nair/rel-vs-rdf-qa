import json

def merge_evaluation_data(file1_path, file2_path, output_path):
    # Load the JSON files
    with open(file1_path, 'r') as f1, open(file2_path, 'r') as f2:
        data1 = json.load(f1)
        data2 = json.load(f2)

    # Create a lookup map from the second JSON for fast access
    # mapping: question_id -> evaluation details
    lookup2 = {
        item['question_id']: item.get('judge_evaluation', {}).get('evaluation', {})
        for item in data2
    }

    merged_results = []

    for item in data1:
        qid = item.get('question_id')
        
        # Extract fields from JSON 1
        judge_eval = item.get('judge_evaluation', {})
        sql_status = judge_eval.get('sql_eval', {}).get('status')
        sparql_status = judge_eval.get('sparql_eval', {}).get('status')

        # Extract fields from JSON 2 (using our lookup map)
        eval_data2 = lookup2.get(qid, {})
        consensus = eval_data2.get('consensus_status')
        perceived_winner = eval_data2.get('perceived_winner')

        # Construct the simplified flat object
        merged_entry = {
            "question_id": qid,
            "db_id": item.get('db_id'),
            "difficulty": item.get('difficulty'),
            "sql_status": sql_status,
            "sparql_status": sparql_status,
            "consensus": consensus,
            "perceived_winner": perceived_winner
        }
        
        merged_results.append(merged_entry)

    # Save the combined data
    with open(output_path, 'w') as f_out:
        json.dump(merged_results, f_out, indent=4)
    
    print(f"Successfully merged {len(merged_results)} entries to {output_path}")

# Usage
judge1_json = "experiments/bird_minidev/results/8/judge_results/judgec_results.json"
judge2_json = "experiments/bird_minidev/results/8/judge_results/13/judge_3_evaluation_results.json"
merged_json = "experiments/bird_minidev/results/8/judge_results/13/merged_output.json"
merge_evaluation_data(judge1_json, judge2_json, merged_json)