from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import UserSchema, GetUserByCodigoSchema
from app.models import Usuario
from app.api.routes.deps import get_session
from app.crud import create_user, get_user_by_codigo

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
async def create_new_user(
    user_create: UserSchema,
    db: AsyncSession = Depends(get_session)
):
    user = await create_user(
        db=db,
        codigo=user_create.codigo,
        email=user_create.email,
        nome=user_create.nome,
        senha=user_create.senha,
        caixa=user_create.caixa,
        is_superuser=user_create.is_superuser
    )
    return JSONResponse(content={"message": "User created successfully"}, status_code=status.HTTP_201_CREATED)

@router.post("/by_codigo")
async def get_user(codigo: GetUserByCodigoSchema, db: AsyncSession = Depends(get_session)):
    user = await get_user_by_codigo(db=db, codigo=codigo.codigo)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return user
