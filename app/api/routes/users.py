from fastapi import APIRouter, HTTPException, status
from app.schemas import UserSchema, LoginRequest, RefreshTokenRequest, GetUserSchema
from app.models import Usuario, RefreshToken
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from tortoise.exceptions import DoesNotExist
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
async def create_user(request: UserSchema):
    user = await Usuario.filter(codigo_usuario=request.codigo_usuario).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma conta vinculada a este código."
        )

    user = await Usuario.filter(email=request.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma conta vinculada a este e-mail."
        )

    hashed_password = get_password_hash(request.senha)
    user = await Usuario.create(
        codigo_usuario=request.codigo_usuario,
        email=request.email,
        nome=request.nome,
        is_superuser=request.is_superuser,
        caixa=request.caixa,
        senha=hashed_password
    )

    return {"message": "Usuário criado com sucesso!"}

@router.post("/login")
async def login(request: LoginRequest):
    try:
        usuario = await Usuario.get(codigo_usuario=request.codigo_usuario)

        if not verify_password(request.senha, usuario.senha):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Código de usuário ou senha incorreto.",
            )

        access_token = create_access_token(data={"sub": usuario.codigo_usuario})
        refresh_token = create_refresh_token(data={"sub": usuario.codigo_usuario})

        expires_at = datetime.utcnow() + timedelta(days=30)

        refresh_token_db = await RefreshToken.create(
            usuario=usuario,
            refresh_token=refresh_token,
            expires_at=expires_at
        )

        return {"access_token": access_token, "refresh_token": refresh_token}

    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de usuário não encontrado.")

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    try:
        refresh_token_db = await RefreshToken.get(refresh_token=request.refresh_token)

        current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        
        if refresh_token_db.is_revoked or refresh_token_db.expires_at < current_time:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado.")

        usuario = await refresh_token_db.usuario

        access_token = create_access_token(data={"sub": usuario.codigo_usuario})

        refresh_token_db.expires_at = current_time + timedelta(days=30)
        await refresh_token_db.save()

        return {"access_token": access_token, "refresh_token": refresh_token_db.refresh_token}

    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")

@router.post("/getUser")
async def get_user(request: GetUserSchema):
    try:
        user = await Usuario.get(codigo_usuario=request.codigo_usuario)

        return {"codigo_usuario": user.codigo_usuario, "nome": user.nome, "email": user.email, "caixa": user.caixa}

    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de usuário não encontrado.")