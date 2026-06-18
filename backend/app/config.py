from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./dev.db"
    jwt_secret: str = "change-me-in-production"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    cors_origin: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


settings = Settings()
