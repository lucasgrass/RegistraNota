from fastapi import APIRouter, HTTPException, status
from app.schemas import UserSchema, GetUserByCodigoSchema, LoginRequest, RefreshTokenRequest
from app.models import Usuario, RefreshToken
from app.crud import create_user
from app.core.security import verify_password, create_access_token, create_refresh_token
from tortoise.exceptions import DoesNotExist
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
async def create_new_user(user_create: UserSchema):
    user = await create_user(
        codigo=user_create.codigo,
        email=user_create.email,
        nome=user_create.nome,
        senha=user_create.senha,
        caixa=user_create.caixa,
        is_superuser=user_create.is_superuser
    )
    return {"message": "Usuário criado com sucesso!"}

@router.post("/login")
async def login(request: LoginRequest):
    try:
        usuario = await Usuario.get(codigo=request.codigo)

        if not verify_password(request.senha, usuario.senha):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código de usuário ou senha incorreto.",
            )

        access_token = create_access_token(data={"sub": usuario.codigo})
        refresh_token = create_refresh_token(data={"sub": usuario.codigo})

        expires_at = datetime.utcnow() + timedelta(days=30)

        refresh_token_db = await RefreshToken.create(
            usuario=usuario,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

    except DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de usuário não encontrado.",
        )

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    try:
        refresh_token_db = await RefreshToken.get(refresh_token=request.refresh_token)

        current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        if refresh_token_db.is_revoked or refresh_token_db.expires_at < current_time:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado.")

        usuario = await refresh_token_db.usuario

        access_token = create_access_token(data={"sub": usuario.codigo})

        refresh_token_db.expires_at = current_time + timedelta(days=30)
        await refresh_token_db.save()

        return {"access_token": access_token, "refresh_token": refresh_token_db.refresh_token}

    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")
