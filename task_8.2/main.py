from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from database import get_db_connection
import asyncpg

app = FastAPI()

class Todo(BaseModel):
    title: str
    description: str

class TodoUpdate(BaseModel):
    title: str
    description: str
    completed: bool

@app.post('/tasks', status_code=201)
async def add_todo(todo: Todo, db: asyncpg.Connection = Depends(get_db_connection)):
    row = await db.fetchrow('''
        INSERT INTO Todo(title, description, completed) VALUES($1, $2, $3)
        RETURNING id, title, description, completed
    ''',todo.title, todo.description, False)
    return dict(row)

@app.get('/tasks/{task_id}')
async def get_task(task_id: int, db: asyncpg.Connection = Depends(get_db_connection)):
    row = await db.fetchrow('''
        SELECT
            title,
            description,
            completed
        FROM Todo
        WHERE id = $1
    ''', task_id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return dict(row)

@app.patch('/tasks/{task_id}')
async def patch_todo(task_id: int, todo: TodoUpdate, db: asyncpg.Connection = Depends(get_db_connection)):
    row = await db.fetchrow('''
        UPDATE Todo
        SET title = $1,
            description = $2,
            completed = $3
        WHERE id = $4
        RETURNING id, title, description, completed
    ''', todo.title, todo.description, todo.completed, task_id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    return dict(row)

@app.delete('/tasks/{task_id}')
async def delete_todo(task_id: int, db: asyncpg.Connection = Depends(get_db_connection)):
    result = await db.execute('''
        DELETE FROM Todo WHERE id = $1
    ''', task_id)

    if result == "DELETE 0":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    return {"message": "Task deleted successfully"}

