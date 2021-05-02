import os
from datetime import datetime, timedelta
from requests import get

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse

from ..utils import is_not_empty, write_to_file
from ..config import settings


router = APIRouter(
    prefix="/ninja",
    tags=["ninja"],
    dependencies=[],
    responses={404: {"description": "Not found!"}},
)


# Kind of ugly solution but it's working...
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CACHE_DIR = CURRENT_DIR.replace('routers', 'cache')
# API URLs
NINJA_CURRENCY_URL = settings.NINJA_CURRENCY_URL
NINJA_ITEM_URL = settings.NINJA_ITEM_URL
# Time until cached data is considered old
TIME_UNTIL_DATA_IS_OLD = settings.NINJA_DATA_OLD  # minutes


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


@router.get("/")
async def get_ninja_pricing(type: str = 'Currency', league: str = 'Ultimatum'):
    ninja_file = get_ninja_filename(type)
    if ninja_file == '':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid item type"
        )

    full_path = CACHE_DIR + '/cached_ninja_data/' + ninja_file

    if is_not_empty(full_path) and age_is_ok(type):
        return FileResponse(full_path)
    else:
        category = NINJA_CURRENCY_URL if type == 'Currency' or type == 'Fragment' else NINJA_ITEM_URL
        ninja_data = get(category, params={
                         'league':  league, 'type': type}).content
        write_to_file(full_path, ninja_data)
        last_updated_dict[type] = datetime.now()
        return HTMLResponse(content=ninja_data)