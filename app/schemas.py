from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class CourseRequest(BaseModel):
    topics: List[str]
    level: str = "beginner"
    preferred_content_types: List[str] = ["video", "article"]
    weekly_hours: int = 3


class Resource(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    url: HttpUrl
    source: str           # "google" | "youtube" | etc.
    content_type: str     # "video" | "article" | "book" | ...
    difficulty: Optional[str] = None
    quality_score: Optional[float] = None
    relevance_score: Optional[float] = None
    educational: bool = True


class Module(BaseModel):
    title: str
    objective: str
    topics: List[str]
    suggested_hours: int
    resources: List[Resource]


class CourseResponse(BaseModel):
    title: str
    overview: str
    level: str
    estimated_weeks: int
    weekly_hours: int
    modules: List[Module]
