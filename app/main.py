from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import CourseRequest, CourseResponse
from .pipeline import run_pipeline

app = FastAPI(title="WeLearn API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "WeLearn backend is running. Visit /docs to try the API."}


@app.post("/api/generate-course", response_model=CourseResponse)
def generate_course(req: CourseRequest):
    course_dict = run_pipeline(req)
    # Pydantic will validate & coerce any remaining types
    return CourseResponse.model_validate(course_dict)
