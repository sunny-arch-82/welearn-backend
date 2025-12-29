from typing import List
from .schemas import Resource
from .llm_client import classify_educational, relevance_score

def apply_educational_filter(resources: List[Resource]) -> List[Resource]:
    kept = []
    for r in resources:
        is_edu = classify_educational(r.title, r.description)
        r.educational = is_edu
        if is_edu:
            kept.append(r)
    return kept

def apply_relevance_filter(resources: List[Resource], query: str, min_score: float = 0.4) -> List[Resource]:
    kept = []
    for r in resources:
        score = relevance_score(query, r.title, r.description)
        r.relevance_score = score
        if score >= min_score:
            kept.append(r)
    return kept
