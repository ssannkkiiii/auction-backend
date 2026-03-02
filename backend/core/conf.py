from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auction"
    BID_EXTEND_MINUTES: int = 2

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
