from pydantic import BaseSettings


class Settings(BaseSettings):
    # Discord
    SECRET_KEY: str

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()