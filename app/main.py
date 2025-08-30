# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.api.routes import router
from app.utils.logger import setup_logging, logger

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="UCDB Chat")

    app.add_middleware(SessionMiddleware, secret_key="meia-zero-2025")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.on_event("startup")
    def startup():
        logger.info("🌐 UCDB Chat iniciado!")
        logger.info("💡 Acesse: http://localhost:8000")

    return app

app = create_app()