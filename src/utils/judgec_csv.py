import argparse
import json
from pathlib import Path
from typing import Any, Dict
import pandas as pd


def flatten(obj: Any, parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
    """
    Recursively flatten dict-like JSON objects.
    - dict -> expand keys
    - list -> if list of primitives join by ' | ', if list of dicts -> json string
    - other -> returned as-is
    """
    items: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items.update(flatten(v, new_key, sep=sep))
    elif isinstance(obj, list):
        if not obj:
            items[parent_key] = ""
        elif all(isinstance(x, (str, int, float, bool, type(None))) for x in obj):
            items[parent_key] = " | ".join("" if x is None else str(x) for x in obj)
        else:
            # Mixed or nested dicts -> keep JSON string
            items[parent_key] = json.dumps(obj, ensure_ascii=False)
    else:
        items[parent_key] = obj
    return items


def json_to_csv(inp: Path, out: Path) -> None:
    data = json.loads(inp.read_text(encoding="utf-8"))
    rows = []
    for entry in data:
        # Ensure one CSV row per question_id (top-level entry)
        flat = flatten(entry)
        rows.append(flat)
    df = pd.DataFrame.from_records(rows)
    # prefer question_id as first column if present
    cols = df.columns.tolist()
    if "question_id" in cols:
        cols = ["question_id"] + [c for c in cols if c != "question_id"]
    df.to_csv(out, index=False)


def main():
    inp = Path("experiments/bird_minidev/results/10/judge_results/3/judge_1_evaluation_results.json")
    out = Path("experiments/bird_minidev/results/10/judge_results/3/judge_1_results.csv")
    json_to_csv(inp, out)
    print(out)


if __name__ == "__main__":
    main()