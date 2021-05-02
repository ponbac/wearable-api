from pydantic import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    FB_PROJECTID: str

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()