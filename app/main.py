from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from app.api.main import api_router
from app.core.config import TORTOISE_ORM

from datetime import datetime
import pytz

SP_TZ = pytz.timezone('America/Sao_Paulo')

app = FastAPI()

app.include_router(api_router, prefix="/api/v1")

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)
