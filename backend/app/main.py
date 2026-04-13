from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.routes.auth import router as auth_router
from app.routes.sessions import router as session_router
from app.routes.ws import router as ws_router


def create_app() -> FastAPI:
    app = FastAPI(title="IntelMedIA Gateway")

    @app.get("/metrics", response_class=PlainTextResponse, include_in_schema=False)
    def metrics() -> str:
        return (
            "# HELP intelmedia_gateway_up IntelMedIA gateway process status\n"
            "# TYPE intelmedia_gateway_up gauge\n"
            "intelmedia_gateway_up 1\n"
        )

    app.include_router(auth_router)
    app.include_router(session_router)
    app.include_router(ws_router)
    return app


app = create_app()
