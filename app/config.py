from pydantic import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    FB_PROJECT_ID: str

    NINJA_CURRENCY_URL: str
    NINJA_ITEM_URL: str
    NINJA_DATA_OLD: int

    POE_STASH_URL: str

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()