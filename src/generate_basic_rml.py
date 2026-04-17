import sqlite3
import os
import json

# =============================================================================
# USER CONFIGURATION
# =============================================================================
DB_IDS = [
    "california_schools", "card_games", "codebase_community", 
    "debit_card_specializing", "european_football_2", "financial", 
    "formula_1", "student_club", "superhero", "thrombosis_prediction", 
    "toxicology"
]

def get_paths(db_id):
    base_dir = "/local/data-ssd/nairs/masters_project"
    
    # INPUT: Source Database
    sqlite_path = f"{base_dir}/data/MINIDEV/dev_databases/{db_id}/{db_id}.sqlite"
    
    # OUTPUT 1: RML File
    rml_path = f"{base_dir}/experiments/bird_minidev_basic/{db_id}/{db_id}.rml.ttl"
    
    # OUTPUT 2: Prefixes JSON (Needed for GRASP)
    json_path = f"{base_dir}/experiments/bird_minidev_basic/{db_id}/prefixes.json"
    
    return sqlite_path, rml_path, json_path

# =============================================================================
# SCRIPT LOGIC
# =============================================================================

def generate_w3c_rml_for_db(db_id):
    sqlite_path, rml_path, json_path = get_paths(db_id)
    
    if not os.path.exists(sqlite_path):
        print(f"⚠️  SKIPPING {db_id}: File not found at {sqlite_path}")
        return

    print(f"Processing {db_id} (Strict W3C + Labels)...")
    base_uri = f"http://{db_id}.org/"
    
    # Initialize Prefix Dictionary for GRASP
    prefix_dict = {
        f"{db_id}_db": f"<{base_uri}>"
    }
    
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]
        
        # Pre-fetch PKs just to know what to use for the Label
        table_pks = {}
        for table in tables:
            cursor.execute(f'PRAGMA table_info("{table}")')
            columns = cursor.fetchall()
            pks = [c[1] for c in columns if c[5] > 0]
            if not pks: pks = [columns[0][1]] # Fallback to first column
            table_pks[table] = pks
            
            # Add table prefix to JSON
            prefix_dict[table] = f"<{base_uri}{table}/>"

        rml_output = []
        rml_output.append(f"@prefix rr: <http://www.w3.org/ns/r2rml#> .")
        rml_output.append(f"@prefix rml: <http://semweb.mmlab.be/ns/rml#> .")
        rml_output.append(f"@prefix ql: <http://semweb.mmlab.be/ns/ql#> .")
        rml_output.append(f"@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .")
        rml_output.append(f"@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .")
        rml_output.append(f"@prefix : <{base_uri}> .")
        rml_output.append("")

        for table in tables:
            cursor.execute(f'PRAGMA table_info("{table}")')
            columns = cursor.fetchall() 
            
            # STRICT MODE: Only get explicit foreign keys
            cursor.execute(f'PRAGMA foreign_key_list("{table}")')
            fks = cursor.fetchall()
            fk_map = {fk[3]: fk[2] for fk in fks}

            pks = table_pks[table]

            # --- LOGICAL SOURCE ---
            rml_output.append(f"######################################################################")
            rml_output.append(f"# Table: {table}")
            rml_output.append(f"######################################################################")
            rml_output.append(f"<#{table}_Mapping>")
            rml_output.append(f"  rml:logicalSource [")
            rml_output.append(f"    rml:source \"{os.path.basename(sqlite_path)}\" ;")
            rml_output.append(f"    rml:referenceFormulation ql:SQL ;")
            col_names = ", ".join([f'"{c[1]}"' for c in columns])
            rml_output.append(f"    rml:query '''SELECT {col_names} FROM \"{table}\"'''")
            rml_output.append(f"  ] ;")
            
            # --- SUBJECT MAP ---
            # W3C Pattern: Table/Col=Val;Col2=Val2
            pk_template_parts = [f"{pk}={{{pk}}}" for pk in pks]
            subject_suffix = ";".join(pk_template_parts)
            subject_template = f"{base_uri}{table}/{subject_suffix}"
            
            rml_output.append(f"  rr:subjectMap [")
            rml_output.append(f"    rr:template \"{subject_template}\" ;")
            rml_output.append(f"    rr:class <{base_uri}{table}>") 
            rml_output.append(f"  ] ;")

            # --- RDFS LABEL (Required for GRASP) ---
            # Pattern: "TableName PrimaryKeyValue"
            label_template = f"{table} {{{pks[0]}}}"
            
            rml_output.append(f"  rr:predicateObjectMap [")
            rml_output.append(f"    rr:predicate rdfs:label ;")
            rml_output.append(f"    rr:objectMap [")
            rml_output.append(f"      rr:template \"{label_template}\" ;")
            rml_output.append(f"      rr:termType rr:Literal")
            rml_output.append(f"    ]")
            rml_output.append(f"  ]") # No semicolon yet

            # --- PREDICATE OBJECT MAPS ---
            pom_blocks = []

            for col in columns:
                col_name = col[1]
                
                # 1. Literal Mapping (Always generated)
                block = []
                block.append(f"  rr:predicateObjectMap [")
                block.append(f"    rr:predicate <{base_uri}{table}#{col_name}> ;")
                block.append(f"    rr:objectMap [ rml:reference \"{col_name}\" ]")
                block.append(f"  ]")
                pom_blocks.append("\n".join(block))

                # 2. Reference Mapping (Only if Explicit FK exists)
                if col_name in fk_map:
                    target_table = fk_map[col_name]
                    
                    # We need target PK name to build W3C URI
                    target_table_pks = table_pks[target_table]
                    target_pk_name = target_table_pks[0]
                    
                    # Target Pattern: TargetTable/TargetPK=LocalFKValue
                    target_template = f"{base_uri}{target_table}/{target_pk_name}={{{col_name}}}"

                    block = []
                    block.append(f"  rr:predicateObjectMap [")
                    block.append(f"    rr:predicate <{base_uri}{table}#ref-{col_name}> ;")
                    block.append(f"    rr:objectMap [")
                    block.append(f"      rr:template \"{target_template}\" ;")
                    block.append(f"      rr:termType rr:IRI")
                    block.append(f"    ]")
                    block.append(f"  ]")
                    pom_blocks.append("\n".join(block))

            # Join blocks with separators
            if pom_blocks:
                rml_output.append(" ;") # Separator after Label
                rml_output.append(" ;\n".join(pom_blocks))
                rml_output.append(" .") # Final dot
            else:
                rml_output.append(" .") 

            rml_output.append("")

        conn.close()

        # --- SAVE RML ---
        os.makedirs(os.path.dirname(rml_path), exist_ok=True)
        with open(rml_path, "w", encoding="utf-8") as f:
            f.write("\n".join(rml_output))
        print(f"   ✓ Generated Strict RML: {rml_path}")

        # --- SAVE PREFIXES JSON ---
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(prefix_dict, f, indent=2)
        print(f"   ✓ Generated Prefixes: {json_path}")

    except Exception as e:
        print(f"   ❌ Error processing {db_id}: {e}")

if __name__ == "__main__":
    for db in DB_IDS:
        generate_w3c_rml_for_db(db)