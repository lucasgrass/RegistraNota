from fastapi import APIRouter, HTTPException, status
from app.schemas import UserSchema, GetUserByCodigoSchema
from app.models import Usuario
from app.crud import create_user, get_user_by_codigo

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
async def create_new_users(user_create: UserSchema):
    user = await create_user(
        codigo=user_create.codigo,
        email=user_create.email,
        nome=user_create.nome,
        senha=user_create.senha,
        caixa=user_create.caixa,
        is_superuser=user_create.is_superuser
    )
    return {"message": "User created successfully"}

@router.post("/by_codigo")
async def get_user(codigo: GetUserByCodigoSchema):
    user = await get_user_by_codigo(codigo.codigo)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
