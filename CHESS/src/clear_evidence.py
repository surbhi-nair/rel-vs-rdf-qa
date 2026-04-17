import json

def clear_evidence_fields(input_file, output_file):
    try:
        # Load the JSON data
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Iterate and modify the "evidence" variable
        for entry in data:
            if "evidence" in entry:
                entry["evidence"] = ""

        # Save the updated JSON data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        print(f"Success! Modified data saved to {output_file}")

    except FileNotFoundError:
        print("Error: The input file was not found.")
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON. Check your file format.")

# Usage
clear_evidence_fields('data/dev/remaining_minidev.json', 'data/dev/remaining_minidev.json')