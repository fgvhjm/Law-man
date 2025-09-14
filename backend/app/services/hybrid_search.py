import json
from retrieval import init_client, search_clauses, format_search_results
from vector_search import VectorStore


def normalize_scores(results):
    if not results:
        return results
    scores = [float(r.get("score", 0.0)) for r in results]
    min_s, max_s = min(scores), max(scores)
    if min_s == max_s:
        for r in results:
            r["norm_score"] = 1.0
    else:
        for r, s in zip(results, scores):
            r["norm_score"] = (s - min_s) / (max_s - min_s)
    return results


def fuse_results(os_results, qdrant_results, alpha=0.5, top_k=10):
    os_results = normalize_scores(os_results)
    qdrant_results = normalize_scores(qdrant_results)
    combined = {}

    # Insert BM25 results first
    for r in os_results:
        cid = r["clause_id"]
        combined[cid] = dict(r)
        combined[cid]["bm25_score"] = r["norm_score"]
        combined[cid]["vec_score"] = 0.0

    # Merge Qdrant results
    for r in qdrant_results:
        cid = r["clause_id"]
        if cid in combined:
            combined[cid]["vec_score"] = r["norm_score"]
            combined[cid]["score"] = max(combined[cid]["score"], r["score"])
        else:
            combined[cid] = dict(r)
            combined[cid]["bm25_score"] = 0.0
            combined[cid]["vec_score"] = r["norm_score"]
            combined[cid]["highlight"] = []

    # Hybrid score
    for r in combined.values():
        r["hybrid_score"] = alpha * r["bm25_score"] + (1 - alpha) * r["vec_score"]

    fused = sorted(combined.values(), key=lambda x: x["hybrid_score"], reverse=True)
    return fused[:top_k]


def hybrid_search(query, top_k=10, alpha=0.5):
    os_client = init_client()
    os_raw = search_clauses(os_client, query, index_name="contracts", size=top_k)
    os_formatted = format_search_results(os_raw)

    vs = VectorStore(reset=False)  # do not reset collection
    qdrant_raw = vs.search(query, top_k=top_k)
    qdrant_formatted = vs.format_qdrant_results(qdrant_raw)

    return fuse_results(os_formatted, qdrant_formatted, alpha=alpha, top_k=top_k)


if __name__ == "__main__":
    query = "insurance coverage"
    results = hybrid_search(query, top_k=10, alpha=0.6)

    with open("hybrid_search_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(results)} hybrid results to hybrid_search_results.json")
    for r in results:
        print(f"Clause: {r['clause_id']} | Hybrid Score: {r['hybrid_score']:.3f} | Heading: {r['heading']}")
