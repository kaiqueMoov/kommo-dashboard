from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.kommo import router as kommo_router
from app.core.database import SessionLocal, engine
from app.models.base import Base

import app.models

app = FastAPI(title="Kommo Dashboard API")


app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "API no ar"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-test")
def db_test():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {"database": "connected", "result": result}
    finally:
        db.close()


@app.get("/app")
def app_page():
    return FileResponse("app/static/dashboard.html")


app.include_router(kommo_router, prefix="/kommo", tags=["kommo"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])