import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from passlib.context import CryptContext

from .schemas.schemas import Snapshot, User, UserInDB

# Init Firestore
cred = credentials.Certificate('firebaseKey.json')
firebase_admin.initialize_app(cred, {
    'projectId': 'poe-currency-ad0db',
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