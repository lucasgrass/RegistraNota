from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist

from app.schemas import CategorySchema
from app.models import Categoria
from app.core.security import validate_access_token

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/")
async def create_category(request: CategorySchema):

    _ = await validate_access_token(request.access_token)

    category = await Categoria.filter(codigo_categoria=request.codigo_categoria).first()
    if category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma categoria vinculada a este código."
        )

    category = await Categoria.create(
        codigo_categoria=request.codigo_categoria,
        descricao=request.descricao,
    )

    return {"message": "Categoria criada com sucesso!"}

@router.get("/")
async def get_category():
    category = await Categoria.all().order_by("codigo_categoria")

    return [category for category in category]