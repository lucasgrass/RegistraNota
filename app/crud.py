from fastapi import HTTPException, status

from sqlalchemy import or_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Usuario
from app.core.security import get_password_hash

async def create_user(db: AsyncSession, codigo: str, email: str, nome: str, senha: str, caixa: int, is_superuser: bool = False):
    result = await db.execute(select(Usuario).filter(or_(Usuario.codigo == codigo, Usuario.email == email)))
    user = result.scalars().first()

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário com o mesmo código ou e-mail já existe."
        )
    else:
        hashed_password = get_password_hash(senha)

        user = Usuario(
            codigo=codigo,
            email=email,
            nome=nome,
            is_superuser=is_superuser,
            caixa=caixa,
            senha=hashed_password
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

async def get_user_by_codigo(db: AsyncSession, codigo:str) -> Usuario:
    result = await db.execute(select(Usuario).filter(Usuario.codigo == codigo))
    user = result.scalars().first()
    return user