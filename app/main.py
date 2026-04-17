from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.kommo import router as kommo_router
from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.user import User
from app.models.lead import Lead
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Kommo Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")




@app.get("/")
def root():
    return {
        "message": "Kommo Dashboard API no ar",
        "docs": "/docs",
        "health": "/health",
        "app": "/app",
    }

@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        print("Tabelas verificadas/criadas com sucesso.")
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")


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