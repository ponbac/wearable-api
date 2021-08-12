from datetime import datetime
import pytz
from typing import Optional
from requests.sessions import Session

from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends, HTTPException, status, Form, Response

from ..config import settings
from ..dependencies import get_current_user
from ..schemas.schemas import UserInDB


# DEPENDENCY - Check that the access token is valid before making a request
def valid_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.expires is not None and datetime.now(pytz.utc) < current_user.expires:
        return current_user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PoE API Access Token has expired, you need to reauthenticate."
        )

router = APIRouter(
    prefix="/official",
    tags=["PoE - API"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

API_URL = 'https://api.pathofexile.com'


def get_api_data(query: str, current_user: Optional[UserInDB] = None):
    with Session() as s:
        if current_user:
            s.headers.update({'User-Agent': f'OAuth {settings.POE_CLIENT_ID}/1.0.0 (contact: ponbac@student.chalmers.se)',
                            'Authorization': f'Bearer {current_user.access_token}'})
        else:
            s.headers.update({'User-Agent': f'OAuth {settings.POE_CLIENT_ID}/1.0.0 (contact: ponbac@student.chalmers.se)'})
        data = s.get(f'{API_URL}{query}')

        return data

# Set rate-limiting headers


def set_headers(api_response):
    # If rate-limit headers are not present return NONE header
    try:
        policy = api_response.headers['x-rate-limit-policy']
        rules = api_response.headers['x-rate-limit-rules']
        client = api_response.headers[f'x-rate-limit-{rules}']
        client_state = api_response.headers[f'x-rate-limit-{rules}-state']
        headers = {'X-Rate-Limit-Policy': policy, 'X-Rate-Limit-Rules': rules,
                   f'X-Rate-Limit': client, f'X-Rate-Limit-State': client_state}

        # Check if currently rate limited
        try:
            retry = api_response.headers['retry-after']
            headers['Retry-After'] = retry
        except:
            headers['Retry-After'] = 'OK'

        return headers
    except:
        return {'X-Rate-Limit-Policy': 'NONE'}


# https://www.pathofexile.com/developer/docs/reference#profile
@ router.get("/profile")
async def get_profile(current_user: UserInDB = Depends(valid_user)):
    res = get_api_data('/profile', current_user)
    headers = set_headers(res)

    return JSONResponse(content=res.json(), headers=headers, status_code=res.status_code)


# https://www.pathofexile.com/developer/docs/reference#characters
@ router.get("/characters")
async def get_character(current_user: UserInDB = Depends(valid_user), name: Optional[str] = None):
    query = '/character' if not name else f'/character/{name}'

    res = get_api_data(query, current_user)
    headers = set_headers(res)

    return JSONResponse(content=res.json(), headers=headers, status_code=res.status_code)


# https://www.pathofexile.com/developer/docs/reference#stashes
@ router.get("/stash")
async def get_stash(current_user: UserInDB = Depends(valid_user), league: str = 'Ultimatum',
 stash_id: Optional[str] = None, substash_id: Optional[str] = None):
    query = f'/stash/{league}'
    if stash_id and substash_id:
        query = query + f'/{stash_id}/{substash_id}'
    elif stash_id and not substash_id:
        query = query + f'/{stash_id}'

    res = get_api_data(query, current_user)
    headers = set_headers(res)

    return JSONResponse(content=res.json(), headers=headers, status_code=res.status_code)


# https://www.pathofexile.com/developer/docs/reference#leagues
@ router.get("/league/ladder")
async def get_league(league: str = 'Ultimatum'):
    query = f'/league/{league}/ladder'

    res = get_api_data(query)
    headers = set_headers(res)

    return JSONResponse(content=res.json(), headers=headers, status_code=res.status_code)