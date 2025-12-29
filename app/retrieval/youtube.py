from typing import List
import httpx

from ..config import settings
from ..schemas import Resource

BASE_URL = "https://www.googleapis.com/youtube/v3/search"


def _build_safe_query(raw: str) -> str:
    """Very simple cleaning + ensure it's educational."""
    base = raw.lower()
    # You can add replacements here if you like, but keep it simple
    return f"{base} tutorial basics"


def search_youtube_educational(query: str, max_results: int = 5) -> List[Resource]:
    if not settings.YOUTUBE_API_KEY:
        return []

    safe_q = _build_safe_query(query)

    params = {
        "key": settings.YOUTUBE_API_KEY,
        "part": "snippet",
        "q": safe_q,
        "type": "video",
        "maxResults": max_results,
        "safeSearch": "strict",
        # IMPORTANT: we do NOT use videoCategoryId with multiple values (that caused 400)
    }

    try:
        resp = httpx.get(BASE_URL, params=params, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(
            f"[YouTube] {e.response.status_code} {e.response.reason_phrase} "
            f"for query: {safe_q}"
        )
        return []
    except Exception as e:
        print(f"[YouTube] Other error for query {safe_q}: {e}")
        return []

    data = resp.json()
    items = data.get("items", [])
    resources: List[Resource] = []

    for item in items:
        id_info = item.get("id", {})
        video_id = id_info.get("videoId")
        if not video_id:
            continue

        snippet = item.get("snippet", {})
        title = snippet.get("title", "")
        description = snippet.get("description", "")
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        resources.append(
            Resource(
                id=f"youtube:{video_id}",
                title=title,
                description=description,
                url=video_url,
                source="youtube",
                content_type="video",
                relevance_score=0.8,
                quality_score=None,
                educational=True,
            )
        )

    return resources
