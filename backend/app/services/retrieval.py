import os
import json
from dotenv import load_dotenv
from opensearchpy import OpenSearch, helpers


# ---------- Init ----------

def init_client():
    """
    Initialize OpenSearch client.
    Tries HTTPS first, falls back to HTTP if SSL fails.
    """
    load_dotenv()
    admin_password = os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD")
    if not admin_password:
        raise ValueError("Missing OPENSEARCH_INITIAL_ADMIN_PASSWORD in .env")

    # Try HTTPS
    try:
        client = OpenSearch(
            hosts=[{"host": "localhost", "port": 9200}],
            http_auth=("admin", admin_password),
            use_ssl=True,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        client.info()  # test connection
        print("Connected to OpenSearch (HTTPS)")
        return client
    except Exception as e:
        print(f"HTTPS connection failed: {e}")
        print("Retrying with HTTP...")

    # Fallback to HTTP
    client = OpenSearch(
        hosts=[{"host": "localhost", "port": 9200}],
        http_auth=("admin", admin_password),
        use_ssl=False, 
        verify_certs=False,
    )
    client.info()  # test connection
    print("Connected to OpenSearch (HTTP)")
    return client



# ---------- Create Index ----------
def create_index(client, index_name="contracts"):
    """Create index with mapping if it doesn't exist."""
    if not client.indices.exists(index=index_name):
        client.indices.create(
            index=index_name,
            body={
                "mappings": {
                    "properties": {
                        "contract_id": {"type": "keyword"},
                        "clause_id": {"type": "keyword"},
                        "heading": {"type": "text"},
                        "text": {"type": "text"},
                        "page": {"type": "integer"},
                        "line_start": {"type": "integer"},
                        "line_end": {"type": "integer"},
                        "lang": {"type": "keyword"},
                        "source": {"type": "keyword"},
                    }
                }
            },
        )
        print(f"Created index: {index_name}")
    else:
        print(f"Index '{index_name}' already exists")


# ---------- Bulk Index ----------
def bulk_index(client, clauses, index_name="contracts", reset=False):
    """
    Bulk index clauses into OpenSearch.
    If reset=True, delete and recreate the index before indexing.
    """
    if reset:
        if client.indices.exists(index=index_name):
            client.indices.delete(index=index_name)
            print(f"Deleted existing index '{index_name}'")
        create_index(client, index_name)  # reuse your existing function
        print(f"Recreated index '{index_name}'")

    # prepare bulk actions
    actions = [
        {
            "_index": index_name,
            "_id": f"{c['contract_id']}#{c['clause_id']}",
            "_source": c,
        }
        for c in clauses
    ]

    helpers.bulk(client, actions, refresh=True)
    print(f"Indexed {len(actions)} clauses into '{index_name}'")


# ---------- Search ----------
def search_clauses(client, query_text, index_name="contracts", size=25):
    """Search clauses with highlighting."""
    query = {
        "size": size,   # <-- now size is configurable
        "query": {"match": {"text": query_text}},
        "highlight": {
            "fields": {
                "text": {"fragment_size": 150, "number_of_fragments": 3}
            }
        },
    }

    results = client.search(index=index_name, body=query)
    return results


# ---------- Format Search Results ----------
def format_search_results(results):
    """
    Convert raw OpenSearch results into clean JSON for the app.
    """
    formatted = []

    for hit in results["hits"]["hits"]:
        src = hit["_source"]

        record = {
            "contract_id": src.get("contract_id"),
            "clause_id": src.get("clause_id"),
            "heading": src.get("heading"),
            "text_snippet": src.get("text")[:400],  # short preview
            "page": src.get("page"),
            "line_range": [src.get("line_start"), src.get("line_end")],
            "lang": src.get("lang", "en"),
            "score": hit.get("_score"),
            "highlight": hit.get("highlight", {}).get("text", []),
        }

        formatted.append(record)

    return formatted



# ---------- Example Runner ----------
if __name__ == "__main__":
    # Step 1: Init client
    client = init_client()

    # Step 2: Ensure index exists
    index_name = "contracts"
    create_index(client, index_name)

    # Step 3: Load JSON file
    json_file = "/Users/amitprasadsingh/Desktop/Lawman/backend/app/services/contract_parsed.json"
    with open(json_file, "r", encoding="utf-8") as f:
        clauses = json.load(f)

    # Step 4: Bulk index
    bulk_index(client, clauses, index_name,reset=True)

    # Step 6: Search
    search_results = search_clauses(client, "insurance coverage", index_name,size=10)

    # Step 5: Format Search Results
    formatted_results = format_search_results(search_results)
    # print((formatted_results))
    # Step 7: Dump formatted results to a JSON file
    
    output_file = "formatted_search_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(formatted_results,f,indent=2)

