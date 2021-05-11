from pydantic import BaseSettings


class Settings(BaseSettings):
    # App Auth
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Firebase Credentials
    type: str
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str

    # poe.ninja
    NINJA_CURRENCY_URL: str
    NINJA_ITEM_URL: str
    NINJA_DATA_OLD: int

    # PoE API OAUTH2
    POE_CLIENT_ID: str
    POE_CLIENT_SECRET: str
    POE_REDIRECT_URL: str

    POE_STASH_URL: str

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()