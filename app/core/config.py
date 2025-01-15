class Settings:
    DATABASE_URL: str = "postgresql+asyncpg://postgres:minecraft1@localhost:5432/registranota"
    API_STR: str = "/api/v1"

    FIRST_SUPERUSER_EMAIL: str = "grassberaldo@gmail.com"
    FIRST_SUPERUSER_PASSWORD: str = "nossoprojeto123"
    FIRST_SUPERUSER_CODIGO: str = "01/01"


settings = Settings()