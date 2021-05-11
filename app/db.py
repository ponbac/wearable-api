import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from passlib.context import CryptContext
from datetime import datetime, timedelta
import json

from .schemas.schemas import Snapshot, User, UserInDB
from .config import settings

# Init Firestore
auth = {
  "type": settings.type,
  "project_id": settings.project_id,
  "private_key_id": settings.private_key_id,
  "private_key": settings.private_key,
  "client_email": settings.client_email,
  "client_id": settings.client_id,
  "auth_uri": settings.auth_uri,
  "token_uri": settings.token_uri,
  "auth_provider_x509_cert_url": settings.auth_provider_x509_cert_url,
  "client_x509_cert_url": settings.client_x509_cert_url
}

# TODO: Remove this ugly workaround, should be able to give initialize_app a dict directly...
with open('firebaseKey.json', 'w+') as file:
    json.dump(auth, file)
with open('firebaseKey.json','r') as file:
    content = file.read()
    content = content.replace('\\\\n', '\\n')
with open('firebaseKey.json','w') as file:
    file.write(content)

cred = credentials.Certificate('firebaseKey.json')
firebase_admin.initialize_app(cred, {
    'projectId': settings.project_id,
})

firebase_db = firestore.client()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
    # return plain_password == hashed_password


def get_password_hash(password):
    return pwd_context.hash(password)
    # return password


def get_firebase_user(username: str):
    user_ref = firebase_db.collection('users').document(username.lower())

    user = user_ref.get()
    if user.exists:
        # print(user.to_dict())
        return UserInDB(**user.to_dict())


def get_snapshot(document_reference: str):
    snapshot_ref = firebase_db.collection('snapshots').document(document_reference)

    snapshot = snapshot_ref.get()
    if snapshot.exists:
        return Snapshot(**snapshot.to_dict())


def create_firebase_user(user: UserInDB):
    users_ref = firebase_db.collection('users')

    users_ref.document(user.username.lower()).set({'username': user.username, 'accountname': user.accountname,
                                                   'poesessid': user.poesessid, 'hashed_password': user.hashed_password, 'disabled': user.disabled, 'friends': []})


def create_snapshot(snapshot: Snapshot):
    snapshots_ref = firebase_db.collection('snapshots')
    users_ref = firebase_db.collection('users')

    # Add snapshot to snapshots collection
    snapshot_ref = snapshots_ref.document()
    snapshot_ref.set(snapshot.dict())

    # Update latest_snapshot_ref for the user
    users_ref.document(snapshot.username.lower()).update(
        {'latest_snapshot_ref': snapshot_ref.id})


def add_friend(friend_to_add: str, current_user: User):
    current_user_ref = firebase_db.collection('users').document(current_user.username.lower())
    current_user_ref.update({u'friends': firestore.ArrayUnion([friend_to_add])})


def authenticate_user(username: str, password: str):
    user = get_firebase_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# TODO: Should not be hardcoded
def set_access_token(username: str, access_token: str, refresh_token: str):
    users_ref = firebase_db.collection('users')
    users_ref.document(username.lower()).update(
        {'access_token': access_token, 'refresh_token': refresh_token, 'expires': datetime.now() + timedelta(days=27, hours=23)})