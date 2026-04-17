import os
import subprocess
import socket
import time

# Configuration
BASE_PATH = "/local/data-ssd/nairs/masters_project"
# Standardizing to your primary path; check if it's bird_minidev or bird-minidev
EXP_DIR = os.path.join(BASE_PATH, "experiments/bird_minidev")

QLEVER_ENDPOINTS = {
    "california_schools": "http://localhost:9002",
    "card_games": "http://localhost:9003",
    "codebase_community": "http://localhost:9004",
    "debit_card_specializing": "http://localhost:9005",
    "european_football_2": "http://localhost:9006",
    "financial": "http://localhost:9007",
    "formula_1": "http://localhost:9008",
    "student_club": "http://localhost:9009",
    "superhero": "http://localhost:9010",
    "thrombosis_prediction": "http://localhost:9011",
    "toxicology": "http://localhost:9012"
}

def is_port_open(port, host='localhost', timeout=1):
    """Check if a specific port is open and responding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except (ConnectionRefusedError, socket.timeout):
            return False

def run_in_env(env_name, command, cwd):
    """Runs a command within a specific conda environment."""
    full_command = f"conda run -n {env_name} --no-capture-output {command}"
    print(f"[{env_name}] Executing: {command} in {cwd}")
    try:
        subprocess.run(full_command, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command in {env_name}: {e}")

def main():
    # Phase 1: Start Qlever for all DBs
    print("--- Phase 1: Starting Qlever (Env: projenv) ---")
    for db_id in QLEVER_ENDPOINTS.keys():
        db_path = os.path.join(EXP_DIR, db_id)
        if os.path.exists(db_path):
            run_in_env("projenv", "qlever start", db_path)
        else:
            print(f"!!! Directory not found: {db_path}")

    # Phase 2: Wait for Ports and Run Grasp
    print("\n--- Phase 2: Verifying Endpoints & Running Grasp (Env: grasprepo) ---")
    for db_id, url in QLEVER_ENDPOINTS.items():
        db_path = os.path.join(EXP_DIR, db_id)
        if not os.path.exists(db_path):
            continue

        # Extract port from URL (e.g., "http://localhost:9002" -> 9002)
        port = int(url.split(":")[-1])
        
        print(f"Checking port {port} for {db_id}...")
        retries = 5
        while retries > 0:
            if is_port_open(port):
                print(f"Port {port} is UP. Proceeding with Grasp.")
                time.sleep(2) # Brief pause for DB stability
                run_in_env("grasprepo", f"grasp data {db_id} --endpoint {url}", db_path)
                run_in_env("grasprepo", f"grasp index {db_id}", db_path)
                break
            else:
                print(f"Port {port} not ready yet. Retrying in 3s... ({retries} retries left)")
                time.sleep(3)
                retries -= 1
        
        if retries == 0:
            print(f"!!! Skipping {db_id}: Qlever port {port} failed to open.")

if __name__ == "__main__":
    main()