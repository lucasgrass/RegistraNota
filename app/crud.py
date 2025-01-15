from fastapi import HTTPException, status
from app.models import Usuario
from app.core.security import get_password_hash

async def create_user(codigo: str, email: str, nome: str, senha: str, caixa: int, is_superuser: bool = False):
    user = await Usuario.filter(codigo=codigo).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma conta vinculada a este código."
        )

    user = await Usuario.filter(email=email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma conta vinculada a este e-mail."
        )

    hashed_password = get_password_hash(senha)
    user = await Usuario.create(
        codigo=codigo,
        email=email,
        nome=nome,
        is_superuser=is_superuser,
        caixa=caixa,
        senha=hashed_password
    )

    return user