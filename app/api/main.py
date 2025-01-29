from fastapi import APIRouter

from app.api.routes import users, categories, notes, sheets, reports


api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(categories.router)
api_router.include_router(notes.router)
api_router.include_router(sheets.router)
api_router.include_router(reports.router)