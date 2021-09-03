from pydantic import BaseSettings


class Settings(BaseSettings):
    # Discord
    DISCORD_TOKEN: str
    DISCORD_API_VERSION: int

    # Deta
    DETA_PROJECT_KEY: str

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()