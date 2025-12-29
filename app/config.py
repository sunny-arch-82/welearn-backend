from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GROQ_API_KEY: str
    LLM_MODEL: str = "llama-3.1-70b-versatile"

    YOUTUBE_API_KEY: str | None = None
    GOOGLE_CSE_API_KEY: str | None = None
    GOOGLE_CSE_ENGINE_ID: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
