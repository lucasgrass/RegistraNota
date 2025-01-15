from app.models import Base  # Importando o Base do seu models.py
from app.core.config import settings
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from alembic import context

# Conectando-se ao banco de dados de forma assíncrona
def get_async_engine():
    return create_async_engine(
        context.config.get_main_option("sqlalchemy.url"),
        echo=True,
    )

def run_migrations_online():
    connectable = get_async_engine()

    # Defina a função que será usada para fazer a conexão
    async def run_migrations():
        async with connectable.connect() as connection:
            # Configuração da sessão assíncrona
            async with connection.begin():
                context.configure(
                    connection=connection,
                    target_metadata=Base.metadata,  # Certifique-se de usar Base
                )

                # Executar migrações assíncronas
                await context.run_migrations()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_migrations())

# Se estiver rodando migrações offline (ex.: em arquivos)
def run_migrations_offline():
    context.configure(
        url=context.config.get_main_option("sqlalchemy.url"),
        target_metadata=Base.metadata,  # Certifique-se de usar Base
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
