from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
from datetime import datetime, timedelta
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
import secrets
from functools import wraps

app = FastAPI()
security = HTTPBearer()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

SECRET_KEY = "new_key_is_kinger"
ALGORITHM = "HS256"
EXPIRES_IN_MINUTES = 45

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserInBD(BaseModel):
    username: str
    hashed_password: str
    roles: list[str]

class UserLogin(BaseModel):
    username: str
    password: str

class Resource(BaseModel):
    id: str
    name: str
    purpose: str

class ResUpdate(BaseModel):
    name: str | None = None
    purpose: str | None = None

    
RESOURCE_BD = [
    Resource(**{"id": "1", "name": "slime", "purpose": "to jump"})
]

USER_BD = [
    UserInBD(**{"username": "Oli", "hashed_password": pwd_context.hash("Bazuka666"), "roles": ["admin"]}),
    UserInBD(**{"username": "Franc", "hashed_password": pwd_context.hash("LOLz_312"), "roles": ["user"]}),
    UserInBD(**{"username": "Kek", "hashed_password": pwd_context.hash("HSR_forever"), "roles": ["guest"]})
]

def create_jwt_token(data: Dict):
    to_encode = data.copy()
    expires = datetime.now() + timedelta(minutes=EXPIRES_IN_MINUTES)
    to_encode.update({"exp": expires})
    return encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
def get_user(username: str):
    for user in USER_BD:
        if user.username == username:
            return user
    return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        user = get_user(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="access token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    
class PermissionChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: UserInBD = Depends(get_current_user)):
        if "admin" in current_user.roles:
            return

        if not any(role in current_user.roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=403,
                detail="Insufficient access rights"
            )

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests"}
    )

@app.post('/register')
@limiter.limit('1/minute')
def create_new_user(request: Request, new_user: UserLogin):
    for user in USER_BD:
        if secrets.compare_digest(user.username, new_user.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        
    hashed_password = pwd_context.hash(new_user.password)

    USER_BD.append(
        UserInBD(username=new_user.username, hashed_password=hashed_password, roles=["guest"])
    )
    return {"message": "New user created"}

@app.post('/login')
@limiter.limit('5/minute')
def login_user(request: Request, user_in: UserLogin):
    user = get_user(user_in.username)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not pwd_context.verify(user_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization failed")
    
    token = create_jwt_token({"sub": user.username})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@app.get('/protected_resource')
def save_route(_: None = Depends(PermissionChecker(["admin", "user"])), current_user: UserInBD = Depends(get_current_user)):
    if current_user:
        return {
            "message": "access granted",
            "user": current_user
        }
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

@app.post('/resource')
def post_item(new_res: Resource, _: None = Depends(PermissionChecker(["admin"]))):
    for res in RESOURCE_BD:
        if res.name == new_res.name:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="That item is already exists")
    
    RESOURCE_BD.append(
        Resource(id=new_res.id, name=new_res.name, purpose=new_res.purpose)
    )
    return {"message": "new item added"}

@app.patch('/resource/{resource_id}')
def patch_item(resource_id: str, patch_res: ResUpdate, _: None = Depends(PermissionChecker(["user"]))):
    for resource in RESOURCE_BD:
        if resource.id == resource_id:

            if patch_res.name is not None:
                resource.name = patch_res.name
            
            if patch_res.purpose is not None:
                resource.purpose = patch_res.purpose

            return resource
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="resource not found")

@app.get('/resource')
def get_resources(_: None = Depends(PermissionChecker(["admin", "user", "guest"]))):
    return RESOURCE_BD
