# probe_reasoning_effort.py
import time
import json
from llm.engine_configs import ENGINE_CONFIGS

CANDIDATES = ["minimal"]  # adjust list

def try_invoke(model_obj, prompt_text="Hello", max_completion_tokens=8):
    """Try common invocation methods used by LangChain wrappers."""
    for method in ("invoke", "generate", "__call__", "chat"):
        fn = getattr(model_obj, method, None)
        if not fn:
            continue
        try:
            if method == "invoke":
                return True, fn(prompt_text)
            if method == "generate":
                # some wrappers expect a list of prompts
                return True, fn([prompt_text])
            if method == "__call__":
                return True, fn(prompt_text)
            if method == "chat":
                return True, fn(prompt_text)
        except Exception as e:
            return False, str(e)
    return False, "No supported invoke method found"

def probe(engine_name: str, candidates=CANDIDATES):
    if engine_name not in ENGINE_CONFIGS:
        raise SystemExit(f"Unknown engine: {engine_name}")
    base = ENGINE_CONFIGS[engine_name]
    constructor = base["constructor"]
    base_params = base.get("params", {}).copy()

    results = {}
    for candidate in candidates:
        params = base_params.copy()
        # ensure small output to reduce cost
        params["max_completion_tokens"] = params.get("max_completion_tokens", 64)
        # merge model_kwargs
        mk = params.get("model_kwargs", {}).copy() if isinstance(params.get("model_kwargs"), dict) else {}
        mk["reasoning_effort"] = candidate
        params["model_kwargs"] = mk

        # Log the params we will try
        print(f"\nTrying reasoning_effort={candidate} with params: {json.dumps(params, indent=2)}")

        try:
            model = constructor(**params)
        except Exception as e:
            results[candidate] = {"constructed": False, "error": f"constructor error: {e}"}
            print("  constructor error:", e)
            continue

        # small sleep to avoid rate-limit bursts
        time.sleep(0.5)

        ok, info = try_invoke(model, prompt_text="Say: OK", max_completion_tokens=8)
        if ok:
            results[candidate] = {"constructed": True, "invoked": True, "response_summary": str(info)[:200]}
            print("  invoke succeeded")
        else:
            results[candidate] = {"constructed": True, "invoked": False, "error": str(info)}
            print("  invoke failed:", info)

    print("\nProbe results:")
    for k, v in results.items():
        print(k, "=>", v)
    return results

if __name__ == "__main__":
    import sys
    engine = sys.argv[1] if len(sys.argv) > 1 else "gpt-5-mini"
    probe(engine)