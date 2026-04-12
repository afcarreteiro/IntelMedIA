from fastapi import FastAPI

from app.routes.auth import router as auth_router
from app.routes.sessions import router as session_router
from app.routes.ws import router as ws_router


def create_app() -> FastAPI:
    app = FastAPI(title="IntelMedIA Gateway")
    app.include_router(auth_router)
    app.include_router(session_router)
    app.include_router(ws_router)
    return app


app = create_app()
