import json
import requests

GRASP_URL = "http://tagus:10001/run"

def call_grasp(question, db="debit_card_specializing", qid=1482, timeout=100, max_timeout=200):
    """Send question to GRASP and return sparql + result with retry on timeout."""
    payload = {
        "task": "sparql-qa",
        "input": question,
        "knowledge_graphs": [db]
    }

    try:
        print("Sending question to GRASP…")
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
    question = "Which of the three segments\u2014SME, LAM and KAM\u2014has the biggest and lowest percentage increases in consumption paid in EUR between 2012 and 2013?"
    output = call_grasp(question=question)
    # save json output to file
    with open("src/query_runners/test_grasp_output.json", "w") as f:
        json.dump(output, f, indent=4)
    print("Output saved to src/query_runners/test_grasp_output.json")

if __name__ == "__main__":
    main()