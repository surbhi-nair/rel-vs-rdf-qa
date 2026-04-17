import json
import requests

# QLEVER_URL = "http://tagus:9005/api"
OUTPUT_FILE = "src/query_runners/sparql_result.json"

import os
import sys

# ensure src/ is on sys.path so we can import execute_sql_sparql
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from execute_sql_sparql import get_qlever_url, get_db_path, QLEVER_ENDPOINTS, BASE_DB_DIR


def run_sparql_query(sparql_query, db_id):
    """
    Sends a SPARQL query to QLever using GET /api with URL-encoded 'query' parameter.
    """
    print("Sending SPARQL query to QLever…")

    qlever_url = get_qlever_url(db_id)
    response = requests.get(
        qlever_url,
        params={"query": sparql_query},
        timeout=60
    )

    response.raise_for_status()
    return response.json()


def main():
    db_id = "debit_card_specializing"

    # sparql_query = """PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>\nSELECT ?czkSum ?eurSum ?difference WHERE {\n  {\n    SELECT ( SUM( xsd:double ( ?cons ) ) AS ?czkSum ) WHERE {\n      ?ym <http://debit_card_specializing.org/yearmonth#Date> ?date ; <http://debit_card_specializing.org/yearmonth#Consumption> ?cons ; <http://debit_card_specializing.org/yearmonth#ref-CustomerID> ?cust .\n      ?cust <http://debit_card_specializing.org/customers#Currency> \"CZK\" .\n      FILTER ( SUBSTR( STR( ?date ) , 1 , 4 ) = \"2012\" )\n    }\n  }\n  {\n    SELECT ( SUM( xsd:double ( ?cons2 ) ) AS ?eurSum ) WHERE {\n      ?ym2 <http://debit_card_specializing.org/yearmonth#Date> ?date2 ; <http://debit_card_specializing.org/yearmonth#Consumption> ?cons2 ; <http://debit_card_specializing.org/yearmonth#ref-CustomerID> ?cust2 .\n      ?cust2 <http://debit_card_specializing.org/customers#Currency> \"EUR\" .\n      FILTER ( SUBSTR( STR( ?date2 ) , 1 , 4 ) = \"2012\" )\n    }\n  }\n  BIND( ( ?czkSum - ?eurSum ) AS ?difference )\n}"""

#     sparql_query = """PREFIX cust: <http://debit_card_specializing.org/customers#>
# PREFIX ym: <http://debit_card_specializing.org/yearmonth#>
# PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

# SELECT ?Consumption
# WHERE {
    
#     ?yearmonth_subject ym:Consumption ?Consumption ;
#                        ym:Date ?Date ;
#                        ym:CustomerID ?CustomerID .

#     ?customer_subject cust:CustomerID ?CustomerID ;
#                       cust:Currency "CZK" .   
#     FILTER (STRSTARTS(STR(?Date), "2012"))
# }
# ORDER BY DESC(xsd:decimal(?Consumption))
# LIMIT 5"""

    sparql_query = """SELECT ( AVG( ?yearSum ) / 12 AS ?avgMonthly ) WHERE {\n  {\n    SELECT ?cust ( SUM( ?val ) AS ?yearSum ) WHERE {\n      ?cons a <http://debitcard.org/schema#MonthlyConsumption> ; <http://debitcard.org/schema#forCustomer> ?cust ; <http://debitcard.org/schema#consumptionValue> ?val ; <http://debitcard.org/schema#date> ?date .\n      ?cust <http://debitcard.org/schema#segment> \"SME\" .\n      FILTER ( ?date >= \"201301\" && ?date <= \"201312\" )\n    }\n    GROUP BY ?cust\n  }\n}"""

    result = run_sparql_query(sparql_query, db_id)
    print(result)
    # Save output to file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=4)

    print(f"Result saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()