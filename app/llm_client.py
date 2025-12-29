from typing import List, Dict, Any
from groq import Groq
import json
import re

from .config import settings
from .schemas import Resource

client = Groq(api_key=settings.GROQ_API_KEY)


def _extract_json(text: str) -> str:
    """Grab the first {...} block to make JSON parsing more robust."""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def chat_completion(
    system: str, user: str, max_tokens: int = 1500, temperature: float = 0.3
) -> str:
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content.strip()


def expand_topics(topics: List[str]) -> List[str]:
    joined = ", ".join(topics)
    system = "You are an expert course designer."
    user = f"""
Expand the following high-level topics into 8–12 concrete subtopics
for a learning path. Return ONLY a JSON array of strings, like:

["Topic A", "Topic B", "Topic C"]

Input topics: {joined}
"""
    text = chat_completion(system, user, max_tokens=512, temperature=0.2)

    # Try JSON first
    try:
        data = json.loads(_extract_json(text))
        out = [s.strip() for s in data if isinstance(s, str)]
        out = [s for s in out if s]
        if out:
            return out
    except Exception:
        pass

    # Fallback: parse bullet / numbered list
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    cleaned: List[str] = []
    for ln in lines:
        ln = ln.strip("-• ")
        ln = re.sub(r"^\d+[\).\-\s]+", "", ln).strip()
        if ln:
            cleaned.append(ln)
    return cleaned[:10] or topics


def organize_course(
    subtopics: List[str],
    resources: List[Resource],
    level: str,
    weekly_hours: int,
) -> Dict[str, Any]:
    simple_resources = [
        {
            "id": r.id,
            "title": r.title,
            "source": r.source,
            "content_type": r.content_type,
        }
        for r in resources
    ]

    system = "You are a senior instructional designer creating structured learning paths."
    user = f"""
Design a course for a learner at **{level}** level.

Subtopics (in order of importance):
{subtopics}

Available resources (id, title, source, type):
{json.dumps(simple_resources, ensure_ascii=False, indent=2)}

Return ONLY valid JSON with the following structure and NOTHING else:

{{
  "title": "Short course title",
  "overview": "2–4 sentence overview of what the learner will achieve.",
  "estimated_weeks": 4,
  "modules": [
    {{
      "title": "Module title",
      "objective": "1–2 sentence learning objective.",
      "topics": ["Subtopic 1", "Subtopic 2"],
      "suggested_hours": {weekly_hours}
    }}
  ]
}}

Make 4–8 modules that roughly cover all subtopics.
"""

    text = chat_completion(system, user, max_tokens=1200, temperature=0.4)

    # Try JSON
    try:
        data = json.loads(_extract_json(text))
        if "modules" not in data or not isinstance(data["modules"], list):
            raise ValueError("Missing modules")
        return data
    except Exception:
        # Robust fallback course if the model messes up the JSON
        modules = []
        for st in subtopics:
            modules.append(
                {
                    "title": st,
                    "objective": f"Understand the fundamentals of {st}.",
                    "topics": [st],
                    "suggested_hours": weekly_hours,
                }
            )
        return {
            "title": f"Custom course on {', '.join(subtopics[:3])}",
            "overview": "Automatically generated course outline (fallback mode).",
            "estimated_weeks": max(1, len(modules) // 3),
            "modules": modules,
        }
