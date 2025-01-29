from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist

from app.schemas import ReportSchema
from app.models import Planilha
from app.core.security import validate_access_token
from app.services.report import criar_pdf_nota_fiscal

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/")
async def create_report(request: ReportSchema):

    codigo_usuario = await validate_access_token(request.access_token)

    sheet = await Planilha.filter(codigo_planilha=request.codigo_planilha, codigo_usuario=codigo_usuario).first()

    if not sheet:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Essa planilha não existe para esse usuário.")

    await criar_pdf_nota_fiscal(codigo_usuario, request.codigo_planilha)

    return {"message": "Relatório criado com sucesso!"}