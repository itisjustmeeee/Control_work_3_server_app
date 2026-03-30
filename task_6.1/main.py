from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    username: str
    password: str

USERS_BD = [
    User(**{"username": "Oli", "password": "Bazuka666"}),
    User(**{"username": "Jas", "password": "DanDan12"}),
    User(**{"username": "Asis", "password": "Baka_13_Sas"})
]

security = HTTPBasic()

async def login_into(credentails: HTTPBasicCredentials = Depends(security)):
    user = await get_user(credentails.username)
    password = credentails.password

    if not user or user.password != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized", headers={"WWW-Authenticate": "Basic"})
    return user

async def get_user(username: str):
    for user in USERS_BD:
        if user.username == username:
            return user
    return None
    
@app.get('/login')
async def get_logged_user(user: User = Depends(login_into)):
    return {
        "secret message": "You got my secret, welcome",
        "user info": user
    }

