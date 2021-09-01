import os
from datetime import datetime, timedelta
from typing import Optional
from requests import get

from fastapi import Depends, FastAPI, HTTPException, status, Form, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

from app.routers import discord_router
from app.schemas.schemas import Token, TokenData, User, UserInDB
from .config import settings


app = FastAPI()
app.include_router(discord_router.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@ app.get("/")
async def index():
    return HTMLResponse(content='<h3>some cool simple stuff, <a href="/docs">/docs</a> for testing</h3>')
