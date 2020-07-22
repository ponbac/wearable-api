from datetime import datetime, timedelta
from typing import Optional
from requests import get
from requests.sessions import Session

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from fastapi import Depends, FastAPI, HTTPException, status, Form, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os


# To get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "ddb4817c2d6c50b9b09c757d8fe018291a70ed41174d29358a89a10dd0a9f012"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Init Firestore
cred = credentials.Certificate('firebaseKey.json')
firebase_admin.initialize_app(cred, {
    'projectId': 'poe-currency-ad0db',
})

firebase_db = firestore.client()


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    accountname: Optional[str] = None
    poesessid: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
    # return plain_password == hashed_password


def get_password_hash(password):
    return pwd_context.hash(password)
    # return password


def get_firebase_user(db, username: str):
    user_ref = db.collection('users').document(username.lower())

    user = user_ref.get()
    if user.exists:
        return UserInDB(**user.to_dict())


def create_firebase_user(db, user: UserInDB):
    users_ref = db.collection('users')

    users_ref.document(user.username.lower()).set({'username': user.username, 'accountname': user.accountname,
                                           'poesessid': user.poesessid, 'hashed_password': user.hashed_password, 'disabled': user.disabled})


def authenticate_user(db, username: str, password: str):
    user = get_firebase_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
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
    user = get_firebase_user(firebase_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@ app.post("/register", response_model=User)
async def register_user(username: str = Form(...), password: str = Form(...), accountname: str = Form(...), poesessid: str = Form(...)):
    user = get_firebase_user(firebase_db, username)
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
        hashed_password=get_password_hash(password),
    )

    create_firebase_user(firebase_db, user)

    return user


@ app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(
        firebase_db, form_data.username, form_data.password)
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


@ app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@ app.get("/")
async def index():
    return HTMLResponse(content='<h3>coolest poe api, /docs for testing</h3>')


# TODO: Split this application up into multiple files in a nice way.
# PoE stash, pricing, and caching related methods below:

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
NINJA_CURRENCY_URL = 'https://poe.ninja/api/data/currencyoverview'
NINJA_ITEM_URL = 'https://poe.ninja/api/data/itemoverview'
POE_STASH_URL = 'https://www.pathofexile.com/character-window/get-stash-items'

TIME_UNTIL_DATA_IS_OLD = 15  # minutes

last_updated_dict = {
    'Currency': None,
    'Fragment': None,
    'Oil': None,
    'Incubator': None,
    'Scarab': None,
    'Fossil': None,
    'Resonator': None,
    'Essence': None,
    'DivinationCard': None,
    'Prophecy': None,
    'SkillGem': None,
    'UniqueMap': None,
    'Map': None,
    'UniqueJewel': None,
    'UniqueFlask': None,
    'UniqueWeapon': None,
    'UniqueArmour': None,
    'Watchstone': None,
    'UniqueAccessory': None,
    'DeliriumOrb': None,
    'Beast': None,
    'Vial': None,
}


def get_ninja_filename(type):
    file = ''

    if type == 'Currency':
        file = 'currency.json'
    elif type == 'Fragment':
        file = 'fragment.json'
    elif type == 'Oil':
        file = 'oil.json'
    elif type == 'Incubator':
        file = 'incubator.json'
    elif type == 'Scarab':
        file = 'scarab.json'
    elif type == 'Fossil':
        file = 'fossil.json'
    elif type == 'Resonator':
        file = 'resonator.json'
    elif type == 'Essence':
        file = 'essence.json'
    elif type == 'DivinationCard':
        file = 'divination_card.json'
    elif type == 'Prophecy':
        file = 'prophecy.json'
    elif type == 'SkillGem':
        file = 'skill_gem.json'
    elif type == 'UniqueMap':
        file = 'unique_map.json'
    elif type == 'Map':
        file = 'map.json'
    elif type == 'UniqueJewel':
        file = 'unique_jewel.json'
    elif type == 'UniqueFlask':
        file = 'unique_flask.json'
    elif type == 'UniqueWeapon':
        file = 'unique_weapon.json'
    elif type == 'UniqueArmour':
        file = 'unique_armour.json'
    elif type == 'Watchstone':
        file = 'watchstone.json'
    elif type == 'UniqueAccessory':
        file = 'unique_accessory.json'
    elif type == 'DeliriumOrb':
        file = 'delirium_orb.json'
    elif type == 'Beast':
        file = 'beast.json'
    elif type == 'Vial':
        file = 'vial.json'

    return file


def age_is_ok(type_to_check):
    if last_updated_dict[type_to_check] is None:
        return False

    past = last_updated_dict[type_to_check]
    present = datetime.now()

    return past > (present - timedelta(minutes=TIME_UNTIL_DATA_IS_OLD))


def is_not_empty(fpath):
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0


def write_to_file(fpath, data_to_write, isImage=False):
    if isImage:
        f = open(fpath, "wb")
        f.write(data_to_write)
    else:
        f = open(fpath, "w+")
        f.write(data_to_write.decode('utf-8'))
    f.close
    print(f'Wrote to {fpath}')


@ app.get("/pricing")
async def get_ninja_pricing(type: str = 'Currency', league: str = 'Harvest'):
    ninja_file = get_ninja_filename(type)
    if ninja_file == '':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item type"
        )
    folder_path = CURRENT_DIR + '/cached_ninja_data'

    full_path = folder_path + '/' + ninja_file

    if is_not_empty(full_path) and age_is_ok(type):
        return FileResponse(full_path)
    else:
        category = NINJA_CURRENCY_URL if type == 'Currency' or type == 'Fragment' else NINJA_ITEM_URL
        ninja_data = get(category, params={
                         'league':  league, 'type': type}).content
        write_to_file(full_path, ninja_data)
        last_updated_dict[type] = datetime.now()
        return HTMLResponse(content=ninja_data)


@ app.get("/stash")
async def get_stash_tab(league: str = 'Harvest', tab: int = 0, account: str = 'poeAccountName', sessid: str = 'PoESessionID'):
    s = Session()

    # Asks for everything else
    s.cookies.set('POESESSID', None)
    s.cookies.set('POESESSID', sessid)

    tab_data = s.get(POE_STASH_URL, cookies=s.cookies, params={
                     'league':  league, 'tabs': 1, 'tabIndex': tab, 'accountName': account}).content

    return HTMLResponse(content=tab_data)


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

    folder_path = CURRENT_DIR + '/cached_images'
    full_path = folder_path + '/' + file_name

    if is_not_empty(full_path):
        return FileResponse(full_path)
    else:
        image = get(path).content
        write_to_file(full_path, image, isImage=True)
        return Response(content=image, media_type='image/png')
