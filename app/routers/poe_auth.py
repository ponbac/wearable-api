from requests.sessions import Session
from datetime import datetime, timedelta
from secrets import token_hex

from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, status, Form

from ..db import get_firebase_user, get_snapshot, create_snapshot, set_access_token
from ..schemas.schemas import Snapshot
from ..config import settings


router = APIRouter(
    tags=["PoE - OAuth2"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

# TODO: Temporary solution
state_dict = {}

TOKEN_URL = 'https://www.pathofexile.com/oauth/token'

# Status code: 405
# {'error': 'invalid_request', 'error_description': 'The request method must be POST when requesting an access token', 'error_uri': 'http://tools.ietf.org/html/rfc6749#section-3.2'}
# Takes a code and exchanges it for an access_token and refresh_token
def code_for_token(code: str):
    # Add headers to follow GGG API guidelines, Session() kind of not needed
    s = Session()
    s.headers.update({'User-Agent': f'OAuth {settings.POE_CLIENT_ID}/1.0.0 (contact: ponbac@student.chalmers.se)'})
    # resp = s.post(TOKEN_URL, params={'client_id': settings.POE_CLIENT_ID, 'client_secret': settings.POE_CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': settings.POE_REDIRECT_URL, 'scope': 'account:profile%20account:characters%20account:stashes'})
    resp = s.post(TOKEN_URL, data={'client_id': settings.POE_CLIENT_ID, 'client_secret': settings.POE_CLIENT_SECRET, 'grant_type': 'authorization_code', 'code': code, 'redirect_uri': settings.POE_REDIRECT_URL, 'scope': 'account:profile%20account:characters%20account:stashes'})

    print(f'Status code: {resp.status_code}')
    print(f'Headers: {resp.headers}')
    resp_json = resp.json()
    print(resp_json)
    if resp.status_code == 200:
        return resp_json['access_token'], resp_json['refresh_token']
    print('Could not exchange code for token!')
    return None, None


# TODO: Should depend on being logged in!
@ router.get("/oauth2callback")
async def handle_oauth2callback(code: str, state: str):
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
        set_access_token(access_token, refresh_token)
        print()

    return HTMLResponse('<h2>OAuth2 Callback!</h2>')


@ router.get("/auth/url")
async def get_auth_url():
    client_id = settings.POE_CLIENT_ID
    response_type = 'code'
    scope = 'account:profile%20account:characters%20account:stashes'
    state = token_hex(16)
    redirect_uri = settings.POE_REDIRECT_URL
    prompt = 'consent'

    # Add generated state to state_dict
    state_dict[state] = 1

    auth_url = f'https://www.pathofexile.com/oauth/authorize?client_id={client_id}&response_type={response_type}&scope={scope}&state={state}&redirect_uri={redirect_uri}&prompt={prompt}'
    return {"url": auth_url}


@ router.post("/auth/test")
async def auth_test(code: str = Form(...), test: str = Form(...)):
    set_access_token('access-test', 'refresh-test')
    return {"code": code, "test": test}