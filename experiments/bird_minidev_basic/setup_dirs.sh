#!/bin/bash
# This script sets up the directory structure for the Bird MiniDev Basic experiment by creating directories for each database ID and initializing the required files just the way its done for the birdm-minidev(semantic RML) version.
# Define the list of database IDs
db_ids=(
    "california_schools"
    "card_games"
    "codebase_community"
    "debit_card_specializing"
    "european_football_2"
    "financial"
    "formula_1"
    "student_club"
    "superhero"
    "thrombosis_prediction"
    "toxicology"
)

# NOTE: You wrote ".tll" in the prompt, but standard RML files use ".ttl" (Turtle).
# I have set it to "ttl" below. Change it to "tll" if your pipeline specifically requires that.
EXT="ttl"

echo "Starting directory setup..."

for id in "${db_ids[@]}"; do
    # 1. Create directory if it doesn't exist
    # -p ensures no error if it already exists
    mkdir -p "$id"
    
    # 2. Create the three required files
    # 'touch' creates an empty file if missing, or updates timestamp if present.
    # It will NOT overwrite existing content.
    touch "$id/$id.rml.$EXT"
    touch "$id/Qleverfile"
    touch "$id/prefixes.json"
    
    echo "✓ Processed: $id"
done

echo "All done!"