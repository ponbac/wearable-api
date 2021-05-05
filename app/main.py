import os
from datetime import datetime, timedelta
from typing import Optional
from requests import get
from jose import JWTError, jwt

from fastapi import Depends, FastAPI, HTTPException, status, Form, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

import app.db as db
from app.utils import is_not_empty, write_to_file
from app.routers import ninja, stash, poe_auth
from app.schemas.schemas import Token, TokenData, User, UserInDB
from .config import settings

# To get a string like this run:
# openssl rand -hex 32
# EXAMPLE KEY, NOT USED IN PROD!
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES # 48 hours


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
app.include_router(poe_auth.router) # official poe api-router
app.include_router(ninja.router) # poe.ninja-router
app.include_router(stash.router) # stash-router

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=2)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@ app.post("/register", response_model=User)
async def register_user(username: str = Form(...), password: str = Form(...), accountname: str = Form(...), poesessid: str = Form(...)):
    user = db.get_firebase_user(username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already in use"
        )
    if len(username) < 3 or len(password) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password has to be over three characters long"
        )

    user = UserInDB(
        username=username,
        accountname=accountname,
        poesessid=poesessid,
        disabled=False,
        hashed_password=db.get_password_hash(password),
    )

    db.create_firebase_user(user)

    return user


@ app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@ app.get("/users/me/", response_model=UserInDB)
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    current_user.hashed_password = 'SECRET'
    return current_user


@ app.post("/users/me/friends/add", response_model=User)
async def add_friend_to_current_user(username_to_add: str = Form(...), current_user: UserInDB = Depends(get_current_active_user)):
    username_to_add = username_to_add.lower()
    user_to_add = db.get_firebase_user(username_to_add)

    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not find that user"
        )
    
    if (username_to_add in current_user.friends) or (username_to_add == current_user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already friends with that user"
        )

    db.add_friend(username_to_add, current_user)

    return JSONResponse({'username': current_user.username, 'added_friend': username_to_add})


@ app.get("/")
async def index():
    return HTMLResponse(content='<h3>coolest poe api, <a href="/docs">/docs</a> for testing</h3>')


# TODO: Move /image into a new resorces router
@ app.get("/image")
async def get_icon(path: str = 'https://web.poecdn.com/image/Art/2DItems/Currency/CurrencyUpgradeMagicToRare.png?v=1187a8511b47b35815bd75698de1fa2a&w=1&h=1&scale=1'):
    if not path.split('.com/')[0] == 'https://web.poecdn':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image link"
        )

    if '/gen/' in path:
        file_name = path.split('/')[-2] + '.png'
    else:
        file_name = path.split('?')[0].split('/')[-1]

    current_dir = os.path.dirname(os.path.realpath(__file__))
    full_path = current_dir + '/cache/cached_images/' + file_name

    if is_not_empty(full_path):
        return FileResponse(full_path)
    else:
        image = get(path).content
        write_to_file(full_path, image, isImage=True)
        return Response(content=image, media_type='image/png')

