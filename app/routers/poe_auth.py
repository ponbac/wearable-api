from requests.sessions import Session
from datetime import datetime, timedelta
from secrets import token_hex

from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi import APIRouter, Depends, HTTPException, status, Form, Response

from ..db import set_access_token
from ..config import settings
from ..dependencies import get_current_user
from ..schemas.schemas import UserInDB


router = APIRouter(
    tags=["PoE - OAuth2"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

# TODO: Temporary solution
state_dict = {}

TOKEN_URL = 'https://www.pathofexile.com/oauth/token'

# Takes a code and exchanges it for an access_token and refresh_token
def code_for_token(code: str):
    # Add headers to follow GGG API guidelines, Session() kind of not needed
    s = Session()
    s.headers.update(
        {'User-Agent': f'OAuth {settings.POE_CLIENT_ID}/1.0.0 (contact: ponbac@student.chalmers.se)'})
    resp = s.post(TOKEN_URL, data={'client_id': settings.POE_CLIENT_ID, 'client_secret': settings.POE_CLIENT_SECRET, 'grant_type': 'authorization_code',
                  'code': code, 'redirect_uri': settings.POE_REDIRECT_URL, 'scope': 'account:profile account:characters account:stashes'})

    resp_json = resp.json()
    if resp.status_code == 200:
        return resp_json['access_token'], resp_json['refresh_token']
    print(f'Could not exchange code for token! Error: {resp_json}')
    return None, None


# TODO: Should depend on being logged in!
@ router.get("/oauth2callback")
async def handle_oauth2callback(code: str, state: str, current_user: UserInDB = Depends(get_current_user)):
    try:
        if state_dict[state]:
            print(f'Found state: {state} with code={code}')
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid state parameter: {state}!'
        )
    access_token, refresh_token = code_for_token(code)
    if access_token is not None and refresh_token is not None:
        set_access_token(current_user.username, access_token, refresh_token)

    return HTMLResponse('<h2>OAuth2 Callback!</h2>')


@ router.get("/auth/url")
async def get_auth_url():
    client_id = settings.POE_CLIENT_ID
    response_type = 'code'
    scope = 'account:profile account:characters account:stashes'
    state = token_hex(16)
    redirect_uri = settings.POE_REDIRECT_URL
    prompt = 'consent'

    # Add generated state to state_dict
    state_dict[state] = 1

    auth_url = f'https://www.pathofexile.com/oauth/authorize?client_id={client_id}&response_type={response_type}&scope={scope}&state={state}&redirect_uri={redirect_uri}&prompt={prompt}'
    return {"url": auth_url}


@ router.get("/auth/test")
async def auth_test():
    s = Session()
    s.headers.update({'User-Agent': f'OAuth {settings.POE_CLIENT_ID}/1.0.0 (contact: ponbac@student.chalmers.se)',
                     'Authorization': 'Bearer ba1c29ad03965900d6a5eef1ab31d4902e591928'})
    res = s.get('https://api.pathofexile.com/stash/SSF%20Ultimatum/0e2cbde323/50d58da4ee')
    print(f'Get Status: {res.status_code}')

    # Forward all rate limit-related headers
    policy = res.headers['x-rate-limit-policy']
    rules = res.headers['x-rate-limit-rules']
    client = res.headers[f'x-rate-limit-{rules}']
    client_state = res.headers[f'x-rate-limit-{rules}-state']
    headers = {'X-Rate-Limit-Policy': policy, 'X-Rate-Limit-Rules': rules, f'X-Rate-Limit': client, f'X-Rate-Limit-State': client_state}
    
    # Check if currently rate limited
    try:
        retry = res.headers['retry-after']
        headers['Retry-After'] = retry
    except:
        headers['Retry-After'] = 'OK'
    return JSONResponse(content=res.json(), headers=headers)
