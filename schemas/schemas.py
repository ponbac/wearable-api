from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    friends: Optional[list] = None
    latest_snapshot_ref: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str
    accountname: str
    poesessid: str


class Snapshot(BaseModel):
    username: str
    value: int
    date: datetime