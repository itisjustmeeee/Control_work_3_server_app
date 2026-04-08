from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import get_db_connection
import asyncpg

app = FastAPI()

class User(BaseModel):
    username: str
    password: str

@app.post('/register')
async def register_user(user: User, db: asyncpg.Connection = Depends(get_db_connection)):
    await db.execute("""
        INSERT INTO users(username, password) VALUES($1, $2)
    """, user.username, user.password)
    
    return {"message": "User registered successfully!"}