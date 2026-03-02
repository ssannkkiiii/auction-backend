from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/auction"
    # Хвилини, на які подовжується час лота при новій ставці (0 = не подовжувати)
    BID_EXTEND_MINUTES: int = 2

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
