from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
from datetime import datetime, timedelta
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from pydantic import BaseModel

app = FastAPI()
security = HTTPBearer()

SECRET_KEY = "new_key_is_kinger"
ALGORITHM = "HS256"
EXPIRES_IN_MINUTES = 45

class User(BaseModel):
    username: str
    password: str

USER_BD = [
    User(**{"username": "Oli", "password": "Bazuka666"}),
    User(**{"username": "Franc", "password": "LOLz_312"}),
    User(**{"username": "Kek", "password": "HSR_forever"})
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

@app.post('/login')
def login_user(user_in: User):
    for user in USER_BD:
        if user.username == user_in.username and user.password == user_in.password:
            token = create_jwt_token({"sub": user_in.username})
            return {
                "access_token": token,
                "token_type": "bearer"
            }
    raise HTTPException(status_code=401, detail="Invalid username or password")

@app.get('/protected_resource')
def save_route(current_user: str = Depends(get_user_token)):
    user = get_user(current_user)
    if user:
        return {
            "message": "access granted",
            "user": user
        }
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")