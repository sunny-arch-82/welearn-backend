from typing import List
import httpx

from ..config import settings
from ..schemas import Resource

BASE_URL = "https://www.googleapis.com/customsearch/v1"
NEGATIVE_TERMS = "-movie -music -sports -entertainment -game"


def google_educational_search(query: str, max_results: int = 5) -> List[Resource]:
    if not (settings.GOOGLE_CSE_API_KEY and settings.GOOGLE_CSE_ENGINE_ID):
        return []

    q = f"{query} (tutorial OR course OR lesson OR guide) {NEGATIVE_TERMS}"

    params = {
        "key": settings.GOOGLE_CSE_API_KEY,
        "cx": settings.GOOGLE_CSE_ENGINE_ID,
        "q": q,
        "num": max_results,
        "safe": "active",
    }

    try:
        resp = httpx.get(BASE_URL, params=params, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(
            f"[GoogleCSE] {e.response.status_code} {e.response.reason_phrase}: "
            f"API error for query: {query}"
        )
        return []
    except Exception as e:
        print(f"[GoogleCSE] Other error for query {query}: {e}")
        return []

    data = resp.json()
    items = data.get("items", [])
    resources: List[Resource] = []

    for item in items:
        url = item.get("link")
        if not url:
            continue

        resources.append(
            Resource(
                id=f"google:{url}",
                title=item.get("title", ""),
                description=item.get("snippet", ""),
                url=url,
                source="google",
                content_type="article",
                relevance_score=0.9,
                quality_score=None,
                educational=True,
            )
        )

    return resources
