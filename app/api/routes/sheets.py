from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist

from app.schemas import SheetSchema
from app.models import Planilha

router = APIRouter(prefix="/sheets", tags=["sheets"])

@router.post("/")
async def create_sheet(request: SheetSchema):
    sheet = await Planilha.filter(codigo_planilha=request.codigo_planilha).first()
    if sheet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe uma planilha vinculada a este código."
        )

    sheet = await Planilha.create(
        codigo_planilha=request.codigo_planilha,
    )

    return {"message": "Planilha criada com sucesso!"}