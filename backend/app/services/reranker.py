from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import json
from hybrid_search import hybrid_search  # <-- import your function

# Load the reranker model
model_name = "BAAI/bge-reranker-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)


def rerank(query, hybrid_results, top_k=10):
    """
    Rerank hybrid results using BGE-Reranker.
    Input: query (str), hybrid_results (list of dicts)
    Output: top_k reranked results (list of dicts with reranker_score added)
    """
    # Extract candidate texts from hybrid search
    candidates = [r.get("text_snippet", "") for r in hybrid_results]

    # Build pairs (query, candidate_text)
    pairs = [(query, c) for c in candidates]

    # Tokenize
    inputs = tokenizer(
        pairs,
        padding=True,
        truncation=True,
        return_tensors="pt",
        max_length=512,
    )

    # Forward pass to get scores
    with torch.no_grad():
        scores = model(**inputs).logits.squeeze(-1)

    # Attach scores back to results
    for r, score in zip(hybrid_results, scores.tolist()):
        r["reranker_score"] = float(score)

    # Sort by reranker_score
    reranked = sorted(hybrid_results, key=lambda x: x["reranker_score"], reverse=True)

    return reranked[:top_k]


if __name__ == "__main__":
    query = "early termination"

    # Step 1: Run hybrid search
    hybrid_results = hybrid_search(query, top_k=20, alpha=0.6)

    # Step 2: Apply reranker
    reranked_results = rerank(query, hybrid_results, top_k=10)

    # Save results
    output_file = "reranked_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(reranked_results, f, indent=2, ensure_ascii=False)

    print(f"Saved reranked results to {output_file}")
    for r in reranked_results[:5]:
        print(f"Clause: {r['clause_id']} | Reranker Score: {r['reranker_score']:.3f} | Heading: {r['heading']}")
