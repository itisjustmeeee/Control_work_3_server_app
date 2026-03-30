from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
import secrets

app = FastAPI()

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS_BD = [
    UserInDB(**{"username": "Oli", "hashed_password": pwd_context.hash("Bazuka666")}),
    UserInDB(**{"username": "Jas", "hashed_password": pwd_context.hash("DanDan12")}),
    UserInDB(**{"username": "Asis", "hashed_password": pwd_context.hash("Baka_13_Sas")})
]

security = HTTPBasic()

async def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = await get_user(credentials.username)

    correct_username = user and secrets.compare_digest(user.username, credentials.username)
    correct_password = user and pwd_context.verify(credentials.password, user.hashed_password)

    if not (correct_username and correct_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized", headers={"WWW-Authenticate": "Basic"})
    return user

async def get_user(username: str):
    for user in USERS_BD:
        if user.username == username:
            return user
    return None
    
@app.post('/register')
async def register_user(user: User):
    for existing_user in USERS_BD:
        if existing_user.username == user.username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="already authorized", headers={"WWW-Authenticate": "Basic"})
    
    hased_password = pwd_context.hash(user.password)

    new_user = UserInDB(
        username = user.username,
        hashed_password= hased_password
    )

    USERS_BD.append(new_user)

    return {
        "message": "new user successfully registrated"
    }

@app.get('/login')
async def login_user(user: UserInDB = Depends(auth_user)):
    return {"message": f'Welcome, {user.username}'}