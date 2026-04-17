from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.kommo import router as kommo_router
from app.core.database import SessionLocal

app = FastAPI(title="Kommo Dashboard API")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
def root():
    return {
        "message": "Kommo Dashboard API no ar",
        "docs": "/docs",
        "health": "/health",
        "app": "/app",
    }


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