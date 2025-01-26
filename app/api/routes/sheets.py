from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist

from app.core.security import validate_token
from app.schemas import SheetSchema, GetSheetSchema
from app.models import Planilha, Usuario

router = APIRouter(prefix="/sheets", tags=["sheets"])

@router.post("/")
async def create_sheet(request: SheetSchema):

    try:
        usuario = await Usuario.get(codigo_usuario=request.codigo_usuario)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário não encontrado.")

    sheet = await Planilha.filter(codigo_planilha=request.codigo_planilha, codigo_usuario=request.codigo_usuario).first()

    if sheet:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe uma planilha vinculada a este código para este usuário.")

    sheet = await Planilha.create(codigo_planilha=request.codigo_planilha, codigo_usuario=usuario)

    return {"message": "Planilha criada com sucesso!"}

@router.post("/last")
async def get_last_sheet(request: GetSheetSchema):

    try:
        usuario = await Usuario.get(codigo_usuario=request.codigo_usuario)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário não encontrado.")

    last_sheet = await Planilha.filter(codigo_usuario=request.codigo_usuario).order_by('-id').first()

    if not last_sheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma planilha encontrada para este usuário.")

    return {
        "id": last_sheet.id,
        "codigo_planilha": last_sheet.codigo_planilha
    }