# Repository Structure

## Top-level files

<!-- - `Dockerfile` - Container image build instructions for a reproducible environment.
- `Makefile` - Convenience targets for common tasks (build, run, test). -->
- `environment.yml` - Conda environment specification for Python dependencies.
- `README.md` - High-level project overview and usage notes.
- `STRUCTURE.md` / `structure.md` - Repository structure notes (this file).
- `.gitignore` - Files and folders ignored by git.

## src/ (evaluation, runners, and utilities)

Repository-level tooling for executing predictions, evaluation, and experiment orchestration.

- `src/grasp_runner.py` - Runner for GRASP experiment. You can specify a given db_id to run the experiment on a specific database, or leave it blank to run on all databases.
- `src/execute_sql_sparql.py` and `src/execute_predicted_sql.py` - Execute SQL / SPARQL predictions against datasets or endpoints.
- `src/evaluate_all_f1.py`, `src/evaluate_sparql_f1.py` - Evaluation scripts computing F1 and related metrics.
- `src/generate_basic_rml.py` - Script to generate basic RML mappings from the sqlite database schema directly.
- `src/judge_llm_1.py` - Script to evaluate LLM judgment for accuracy(sql vs sparql given ground truth query and outputs)
- `src/judge_llm_2.py` - Script to evaluate LLM judgment for accuracy(sql vs sparql given ground truth output, query not given)
- `src/judge_llm_3.py` - Script to evaluate LLM judgment for preference(sql vs sparql, ground truth not given)
- `src/cost_calculation/` - Cost computation scripts for LLM API usage (`calculate_costs_grasp.py`, `cost_judgec.py`).
- `src/query_runners/` - Query-runner test scripts to run a single query against a database or SPARQL endpoint for debugging.
- `src/utils/` - Small utilities used across scripts (CSV helpers, JSON merge, DB setup, etc.).

## data/ (datasets)

- `data/BIRD/minidev/` - Path for Mini-dev dataset and metadata used in experiments
	- `mini_dev_sqlite.json` - Contains the gold truth SQL queries for each question.
- CHESS-specific input data lives under `CHESS/data/`.

## experiments/ 
Contains the main experiment folders and their outputs.
- `experiments/bird_minidev/` - main BIRD mini-dev experiment folder, containing:
	- `gpt5-mini.yaml` - config for GRASP runs
	- `morphkgc_config.ini` - config for morph-KGC runs
	- 11 database subfolders (`california_schools/`, `card_games` etc.) each contains:
		- RML file mapping the relational data to RDF
		- `Qleverfile` - configuration for Qlever to run on the generated RDF data.
		- `prefixes.json` - JSON file containing prefixes used in GRASP evaluation
	- `results/` - holds all results from GRASP runs and evaluation results
		- `8` - contains results from experiments done with evidence
		- `10` - contains results from experiments done without evidence

## Key Result Files:
- `experiments/bird_minidev/results/8/f1_all_scores.json` - Contains the **F1 scores** for all evaluated questions for the experiment with evidence.
- `experiments/bird_minidev/results/8/judge_results/judgec_results.json` - Contains the LLM-Judge(*Accuracy*) results for the experiments with evidence.
- `experiments/bird_minidev/results/8/judge_results/13/judge_3_evaluation_results.json` - Contains the LLM-Judge(*Preference*) results for the experiments with evidence.
- `experiments/bird_minidev/results/8/judge_results/13/merged_output.json` - Contains the merged output of the LLM-Judge(*Preference*) results along with the LLM-Judge(*Accuracy*) results for the experiments with evidence.
- `CHESS/results/dev` - Contains the results from CHESS experiment alone.

## CHESS

- `CHESS/README.md` - CHESS-specific documentation.
- `CHESS/requirements.txt` - Python dependencies for CHESS components.
- `CHESS/env.example`, `CHESS/dotenv_copy` - Environment variable examples.
- `CHESS/run/` - Shell scripts and YAML configs for running CHESS experiments:
	- `run_preprocess.sh`, `run_main_ir_cg_ut.sh`, `run_main_ir_ss_cg.sh` - top-level runners.
	- `configs/*.yaml` - experiment configuration variants
- `CHESS/templates/` - Prompt and template resources used by LLM agents.
- `CHESS/images/` - Diagrams and illustration images for docs and README.

### CHESS/src/

Core CHESS code and modules:

- `CHESS/src/main.py` - CHESS orchestration / entry point.
- `CHESS/src/preprocess.py` - Data preprocessing utilities.
- `CHESS/src/generate_remaining_inputs.py` - Data generation helper.
- `CHESS/src/calculate_costs.py`, `CHESS/src/chess_cost_stepwise.py` - Cost calculations.
- `CHESS/src/combine_predictions.py` - Utility to merge model outputs.
- `CHESS/src/threading_utils.py` - Concurrency helpers.

Subpackages:
- `CHESS/src/llm/` - LLM config, prompts, parsers, and model wrappers (`engine_configs.py`, `prompts.py`, `parsers.py`, `models.py`).
- `CHESS/src/database_utils/` - Schema parsing, SQL parsing, execution, and catalog/value helpers.
- `CHESS/src/workflow/` - Agent framework and workflows (agents like schema selector, information retriever, candidate generator, unit tester).
- `CHESS/src/runner/` - Runtime managers, logging, and task orchestration (`run_manager.py`, `logger.py`, `database_manager.py`, `task.py`).
