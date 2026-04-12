from fastapi import FastAPI

from app.routes.auth import router as auth_router


def create_app() -> FastAPI:
    app = FastAPI(title="IntelMedIA Gateway")
    app.include_router(auth_router)
    return app


app = create_app()
