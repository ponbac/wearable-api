from datetime import datetime
from typing import Optional
from requests import get

from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException, status, Form, Response

from ...config import settings
from ..schemas.schemas import UserInDB


router = APIRouter(
    prefix="/discord",
    tags=["Discord"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

BASE_URL = f'https://discord.com/api/v{settings.DISCORD_API_VERSION}'
AUTH_HEADERS = {'Authorization': f'Bot {settings.DISCORD_TOKEN}', 'User-Agent': 'DiscordBot (https://www.wear.backman.app, 0.0.1)'}


@ router.get("/test")
async def test(id: str = '107771609095376896'):
    response = get(f'{BASE_URL}/guilds/{id}/members?limit=500', headers=AUTH_HEADERS)

    return JSONResponse(content=response.json())