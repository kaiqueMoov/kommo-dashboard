from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/app")
def app_page():
    return FileResponse("app/static/dashboard.html")