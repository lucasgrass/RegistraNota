from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist

from app.schemas import NoteSchema, UserNotesSchema
from app.models import Nota, Usuario, Categoria, Planilha


router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("/")
async def create_note(request: NoteSchema):
    try:
        user = await Usuario.get(codigo_usuario=request.codigo_usuario)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    try:
        category = await Categoria.get(codigo_categoria=request.codigo_categoria)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")

    try:
        sheet = await Planilha.get(codigo_planilha=request.codigo_planilha)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planilha não encontrada.")

    new_nota = await Nota.create(
        imagem=request.imagem,
        data=request.data,
        valor=request.valor,
        codigo_categoria=category,
        codigo_usuario=user,
        codigo_planilha=sheet
    )

    return {
        "message": "Nota criada com sucesso.",
        "nota": {
            "id": new_nota.id,
            "imagem": new_nota.imagem,
            "data": new_nota.data,
            "valor": new_nota.valor
        }
    }

@router.post("/last")
async def get_last_notes(request: UserNotesSchema):
    user = await Usuario.filter(codigo_usuario=request.codigo_usuario).exists()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    last_notes = await Nota.filter(codigo_usuario=request.codigo_usuario).order_by("-created_at").limit(10)

    if not last_notes:
        raise HTTPException(status_code=204, detail="Não há notas para esse usuário.")

    return last_notes

@router.post("/count")
async def count_notes(request: UserNotesSchema):
    user = await Usuario.filter(codigo_usuario=request.codigo_usuario).exists()
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    total_notes = await Nota.filter(codigo_usuario=request.codigo_usuario).count()

    return {"total_notes": total_notes}