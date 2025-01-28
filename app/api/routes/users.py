from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import atomic

from app.schemas import UserSchema, LoginRequest, RefreshTokenRequest, GetUserSchema, AddCashRegisterSchema
from app.models import Usuario, RefreshToken
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, validate_access_token

from datetime import datetime, timedelta, timezone
import pytz

saopaulo_tz = pytz.timezone("America/Sao_Paulo")

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

        existing_refresh_token = await RefreshToken.get_or_none(usuario=usuario, is_revoked=False)
        if existing_refresh_token:
            existing_refresh_token.is_revoked = True
            await existing_refresh_token.save()

        access_token = create_access_token(data={"sub": usuario.codigo_usuario})
        refresh_token = create_refresh_token(data={"sub": usuario.codigo_usuario})

        expires_at = datetime.now(saopaulo_tz) + timedelta(days=30)

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
        # Buscando o refresh token no banco
        refresh_token_db = await RefreshToken.get(refresh_token=request.refresh_token)

        current_time = datetime.now(saopaulo_tz)
        if refresh_token_db.is_revoked or refresh_token_db.expires_at < current_time:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado.")

        # Recuperando o usuário
        usuario = await refresh_token_db.usuario

        # Criando novo access token
        access_token = create_access_token(data={"sub": usuario.codigo_usuario})

        # Estendendo a expiração do refresh token
        refresh_token_db.expires_at = current_time + timedelta(days=30)
        await refresh_token_db.save()

        return {"access_token": access_token, "refresh_token": refresh_token_db.refresh_token}

    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")

@router.post("/getUser")
async def get_user(request: GetUserSchema):
    try:
        codigo_usuario = await validate_access_token(request.access_token)
        
        user = await Usuario.get(codigo_usuario=codigo_usuario)

        return {"codigo_usuario": user.codigo_usuario, "nome": user.nome, "email": user.email, "caixa": user.caixa, "is_superuser": user.is_superuser}

    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de usuário não encontrado.")

@router.post("/CashRegister")
@atomic()
async def add_cash_register(request: AddCashRegisterSchema):

    codigo_usuario = await validate_access_token(request.access_token)

    user = await Usuario.get(codigo_usuario=codigo_usuario)

    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Apenas administradores podem mudar o caixa de outra pessoa.")

    try:
        add_user = await Usuario.get(codigo_usuario=request.add_codigo_usuario)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Código de usuário não encontrado.")

    try:
        valor_float = float(request.adicionar_caixa.replace(",", "."))
        valor_centavos = int(valor_float * 100)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valor inválido.")

    add_user.caixa += valor_centavos
    await add_user.save()

    return {"caixa": add_user.caixa, "message": "Valor adicionado ao caixa com sucesso!"}