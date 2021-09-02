from datetime import datetime
from typing import Optional
from requests.sessions import Session

from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException, status, Form, Response

from ..config import settings
from ..schemas.schemas import UserInDB
from ..discord_bot.client import DiscordClient


router = APIRouter(
    prefix="/discord",
    tags=["Discord"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


@ router.get("/test")
async def test(id: str = 'Donkadink'):
    return JSONResponse(content='{}')