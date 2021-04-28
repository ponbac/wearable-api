from requests.sessions import Session
from datetime import datetime, timedelta

from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, status, Form

from ..db import get_firebase_user, get_snapshot, create_snapshot
from ..schemas.schemas import Snapshot


router = APIRouter(
    prefix="/stash",
    tags=["stash"],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)

POE_STASH_URL = 'https://www.pathofexile.com/character-window/get-stash-items'


@ router.get("/")
async def get_stash_tab(league: str = 'Ultimatum', tab: int = 0, account: str = 'poeAccountName', sessid: str = 'PoESessionID'):
    s = Session()

    # Asks for everything else
    s.cookies.set('POESESSID', None)
    s.cookies.set('POESESSID', sessid)

    # Add headers to bypass Cloudflare
    s.headers.update({'User-Agent': 'PostmanRuntime/7.26.10', 'Accept': '*/*', 'Connection': 'keep-alive'})

    tab_data = s.get(POE_STASH_URL, cookies=s.cookies, params={
                     'league':  league, 'tabs': 1, 'tabIndex': tab, 'accountName': account}).content

    return HTMLResponse(content=tab_data)


@ router.get("/snapshot/latest", response_model=Snapshot)
async def get_latest_snapshot(username: str):
    user = get_firebase_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not find that user"
        )

    latest_snapshot = get_snapshot(user.latest_snapshot_ref)
    if not latest_snapshot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user does not have any snapshots"
        )

    return latest_snapshot


@ router.post("/snapshot/add", response_model=Snapshot)
async def add_snapshot(username: str = Form(...), value: int = Form(...)):
    user = get_firebase_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not find that user"
        )

    snapshot = Snapshot(username=username, value=value, date=datetime.now())
    create_snapshot(snapshot)

    return snapshot