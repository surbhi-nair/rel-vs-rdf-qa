import pandas as pd
from pathlib import Path
import sqlite3

# with sqlite3.connect(db) as conn:
#     df = pd.read_sql_query(q, conn)
# from execute_sql_sparql import get_db_path, BASE_DB_DIR
BASE_DB_DIR = Path("data/MINIDEV/dev_databases")
def get_db_path(db_id):
    """Build the SQLite file path from db_id."""
    return BASE_DB_DIR / db_id / f"{db_id}.sqlite"

def func():
    db_id = "card_games"
    db = get_db_path(db_id)
    # q = "SELECT T2.Consumption FROM customers AS T1 INNER JOIN yearmonth AS T2 ON T1.CustomerID = T2.CustomerID WHERE T1.Currency = 'CZK' AND SUBSTR(T2.Date, 1, 4) = '2012' ORDER BY T2.Consumption DESC LIMIT 1;"
    q = "SELECT DISTINCT T1.name\nFROM cards AS T1\nINNER JOIN foreign_data AS T2 ON T1.uuid = T2.uuid\nWHERE (T1.types = 'Artifact' OR T1.originalType LIKE '%Artifact%' OR T1.type LIKE '%Artifact%')\n  AND (\n    (T1.colors IS NOT NULL AND T1.colors LIKE '%B%')\n    OR (T1.colorIdentity IS NOT NULL AND T1.colorIdentity LIKE '%B%')\n    OR (T1.colorIndicator IS NOT NULL AND T1.colorIndicator LIKE '%B%')\n  );"

    with sqlite3.connect(db) as conn:
        df = pd.read_sql_query(q, conn)
        return {
            "columns": df.columns.tolist(),
            "rows": df.values.tolist(),
            "col_count": len(df.columns),
            "row_count": len(df)
        }

res = func()
print(res)