from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from sqlmodel import select

from app import crud
from app.models import Usuario
from app.schemas import UserSchema
from app.core.config import settings
from app.core.security import get_password_hash

engine = create_async_engine(settings.DATABASE_URL)


async def init_db(session: AsyncSession) -> None:
    result = await session.execute(
        select(Usuario).where(Usuario.email == settings.FIRST_SUPERUSER_EMAIL)
    )
    user = result.scalars().first()

    if not user:
        user_in = UserSchema(
            codigo=settings.FIRST_SUPERUSER_CODIGO,
            email=settings.FIRST_SUPERUSER_EMAIL,
            senha=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_superuser=True,
            nome="Admin",
            caixa=0,
        )

        await crud.create_user(
            db=session,  # Passando a sessão corretamente
            codigo=user_in.codigo,
            email=user_in.email,
            nome=user_in.nome,
            senha=user_in.senha,
            caixa=user_in.caixa,
            is_superuser=user_in.is_superuser
        )
