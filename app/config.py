from pydantic import BaseSettings


class Settings(BaseSettings):
    # Discord
    DISCORD_TOKEN: str

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()