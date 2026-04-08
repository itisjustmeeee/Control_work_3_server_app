import asyncpg

DATABASE_URL = "postgresql://postgres:GL19Apw8Nb2@localhost:5432/database_server_app"

async def get_db_connection():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()