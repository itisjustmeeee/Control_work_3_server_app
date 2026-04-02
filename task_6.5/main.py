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

app = FastAPI()
security = HTTPBearer()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

SECRET_KEY = "new_key_is_kinger"
ALGORITHM = "HS256"
EXPIRES_IN_MINUTES = 45

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserIn(BaseModel):
    username: str
    password: str

class UserInBD(BaseModel):
    username: str
    hashed_password: str

USER_BD = [
    UserInBD(**{"username": "Oli", "hashed_password": pwd_context.hash("Bazuka666")}),
    UserInBD(**{"username": "Franc", "hashed_password": pwd_context.hash("LOLz_312")}),
    UserInBD(**{"username": "Kek", "hashed_password": pwd_context.hash("HSR_forever")})
]

def create_jwt_token(data: Dict):
    to_encode = data.copy()
    expires = datetime.now() + timedelta(minutes=EXPIRES_IN_MINUTES)
    to_encode.update({"exp": expires})
    return encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        return username
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="access token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
    
def get_user(username: str):
    for user in USER_BD:
        if user.username == username:
            return user
    return None

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests"}
    )

@app.post('/register')
@limiter.limit('1/minute')
def create_new_user(request: Request, new_user: UserIn):
    for user in USER_BD:
        if secrets.compare_digest(user.username, new_user.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        
    hashed_password = pwd_context.hash(new_user.password)

    USER_BD.append(
        UserInBD(username=new_user.username, hashed_password=hashed_password)
    )
    return {"message": "New user created"}

@app.post('/login')
@limiter.limit('5/minute')
def login_user(request: Request, user_in: UserIn):
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
def save_route(current_user: str = Depends(get_user_token)):
    user = get_user(current_user)
    if user:
        return {
            "message": "access granted",
            "user": user
        }
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")