from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse

MODE = os.getenv("MODE", "DEV")

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "new_admin_33")

security = HTTPBasic()

async def auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, DOCS_USER)
    correct_password = secrets.compare_digest(credentials.password, DOCS_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized", headers={"WWW-Authenticate": "Basic"})

if MODE not in ["DEV", "PROD"]:
    raise ValueError("Invalid MODE")
    
if MODE == "DEV":
    @app.get('/docs', include_in_schema=False)
    async def new_docs(credentials: HTTPBasicCredentials = Depends(security)):
        await auth(credentials)
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

    @app.get('/openapi.json', include_in_schema=False)
    async def new_openapi_json(credentials: HTTPBasicCredentials = Depends(security)):
        await auth(credentials)
        return JSONResponse(app.openapi())

    @app.get('/test')
    async def test():
        return {"message": "success"}