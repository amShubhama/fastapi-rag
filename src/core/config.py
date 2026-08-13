from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str
    database_url: str
    ollama_url: str
    model: str
    user_id: str

    class Config:
        env_file = ".env"


settings = Settings()
