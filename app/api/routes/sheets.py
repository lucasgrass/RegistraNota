from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist

from app.core.security import validate_access_token
from app.schemas import SheetSchema, GetSheetSchema
from app.models import Planilha, Usuario

router = APIRouter(prefix="/sheets", tags=["sheets"])

@router.post("/")
async def create_sheet(request: SheetSchema):

    codigo_usuario = await validate_access_token(request.access_token)
    
    usuario = await Usuario.filter(codigo_usuario=codigo_usuario).first()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário não encontrado.")

    sheet = await Planilha.filter(codigo_planilha=request.codigo_planilha, codigo_usuario=codigo_usuario).first()

    if sheet:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe uma planilha vinculada a este código para este usuário.")

    sheet = await Planilha.create(codigo_planilha=request.codigo_planilha, codigo_usuario=usuario)

    return {"message": "Planilha criada com sucesso!"}

@router.post("/last")
async def get_last_sheet(request: GetSheetSchema):

    codigo_usuario = await validate_access_token(request.access_token)

    last_sheet = await Planilha.filter(codigo_usuario=codigo_usuario).order_by('-id').first()

    if not last_sheet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma planilha encontrada para este usuário.")

    return {
        "id": last_sheet.id,
        "codigo_planilha": last_sheet.codigo_planilha
    }