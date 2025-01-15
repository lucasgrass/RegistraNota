from tortoise import Tortoise
from app.core.config import TORTOISE_ORM

async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    print("Banco de dados inicializado.")

async def close_db():
    await Tortoise.close_connections()