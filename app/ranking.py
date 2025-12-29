from typing import List
from .schemas import Resource, ContentType

def rank_resources(
    resources: List[Resource],
    preferred_content_types: List[ContentType],
) -> List[Resource]:
    def score(res: Resource) -> float:
        rel = res.relevance_score or 0.0
        qual = res.quality_score or 0.7  # default
        type_bonus = 0.1 if res.content_type in preferred_content_types else 0.0
        return 0.6 * rel + 0.3 * qual + 0.1 * type_bonus

    return sorted(resources, key=score, reverse=True)
