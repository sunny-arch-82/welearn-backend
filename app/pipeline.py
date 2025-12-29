from typing import List

from .schemas import (
    CourseRequest,
    Resource,
    Module,
)
from .llm_client import expand_topics, organize_course
from .retrieval.google_search import google_educational_search
from .retrieval.youtube import search_youtube_educational


def run_pipeline(req: CourseRequest) -> dict:
    print("🚀 Running WeLearn Pipeline...")

    # 1) Expand topics
    subtopics = expand_topics(req.topics)
    print("Expanded Topics:", subtopics)

    # 2) Retrieve resources
    all_resources: List[Resource] = []
    seen_urls: set[str] = set()

    for topic in subtopics:
        print(f"\n🔍 Searching resources for: {topic}")

        # Google (articles)
        g_res = google_educational_search(topic, max_results=5)
        if g_res:
            print(f"  ✓ Google results: {len(g_res)}")
        else:
            print("  ✗ Google returned nothing.")

        # YouTube (videos), conditional on user preference
        y_res: List[Resource] = []
        if "video" in req.preferred_content_types:
            y_res = search_youtube_educational(topic, max_results=5)
            if y_res:
                print(f"  ✓ YouTube results: {len(y_res)}")
            else:
                print("  ✗ YouTube returned nothing.")

        for r in (*g_res, *y_res):
            if r.url in seen_urls:
                continue
            seen_urls.add(r.url)
            all_resources.append(r)

    # 3) If absolutely nothing was found → build simple offline course
    if not all_resources:
        print("⚠ No external resources found, returning minimal skeleton.")
        estimated_weeks = max(1, len(subtopics) // 3)
        simple_modules = [
            {
                "title": st,
                "objective": f"Understand the basics of {st}.",
                "topics": [st],
                "suggested_hours": req.weekly_hours,
            }
            for st in subtopics
        ]
        modules_with_resources = _attach_resources_to_modules(
            simple_modules, all_resources
        )
        return {
            "title": f"Custom course on {', '.join(req.topics)}",
            "overview": "Auto-generated course outline. No external links were found (API limitations).",
            "level": req.level,
            "estimated_weeks": estimated_weeks,
            "weekly_hours": req.weekly_hours,
            "modules": modules_with_resources,
        }

    # 4) Rank & trim resources
    ranked = sorted(
        all_resources,
        key=lambda r: (r.relevance_score or 0.5, r.quality_score or 0.5),
        reverse=True,
    )
    ranked = ranked[:40]

    # 5) Ask LLM to organize into modules (title, overview, modules list)
    course_outline = organize_course(subtopics, ranked, req.level, req.weekly_hours)

    # 6) Attach actual Resource objects to each module algorithmically
    modules_with_resources = _attach_resources_to_modules(
        course_outline["modules"], ranked
    )

    # 7) Build final dict that matches CourseResponse
    return {
        "title": course_outline["title"],
        "overview": course_outline["overview"],
        "level": req.level,
        "estimated_weeks": course_outline["estimated_weeks"],
        "weekly_hours": req.weekly_hours,
        "modules": modules_with_resources,
    }


def _attach_resources_to_modules(
    modules: List[dict], resources: List[Resource]
) -> List[Module]:
    modules_out: List[Module] = []

    for m in modules:
        m_topics = [t.lower() for t in m.get("topics", [])]
        matched: List[Resource] = []

        for r in resources:
            haystack = f"{r.title} {r.description}".lower()
            if any(t in haystack for t in m_topics):
                matched.append(r)

        # Fallback: at least some resources per module
        if not matched and resources:
            matched = resources[:3]

        modules_out.append(
            Module(
                title=m["title"],
                objective=m["objective"],
                topics=m["topics"],
                suggested_hours=m["suggested_hours"],
                resources=matched,
            )
        )

    return modules_out
