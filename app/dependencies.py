
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt

from fastapi.security.oauth2 import OAuth2PasswordBearer

from app.schemas.schemas import TokenData
from app.config import settings
import app.db as db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.get_firebase_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user