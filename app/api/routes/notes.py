from fastapi import APIRouter, HTTPException, status, UploadFile, Form
from tortoise.exceptions import DoesNotExist

from app.schemas import NoteSchema, UserNotesSchema, SaveNoteSchema
from app.models import Nota, Usuario, Categoria, Planilha
from app.services.gcs import upload_to_gcs, exclude_from_gcs
from app.services.scan import execute_scan
from datetime import datetime


router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("/last")
async def get_last_notes(request: UserNotesSchema):

    user = await Usuario.filter(codigo_usuario=request.codigo_usuario).exists()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    last_notes = await Nota.filter(codigo_usuario=request.codigo_usuario).order_by("-created_at").limit(10)

    if not last_notes:
        raise HTTPException(status_code=204, detail="Não há notas para esse usuário.")

    return {
        "status": "success",
        "message": f"Últimas notas de {request.codigo_usuario}",
        "data": last_notes
    }


@router.post("/count")
async def count_notes(request: UserNotesSchema):
    user = await Usuario.filter(codigo_usuario=request.codigo_usuario).exists()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    total_notes = await Nota.filter(codigo_usuario=request.codigo_usuario).count()

    return {"total_notes": total_notes}

@router.post("/process")
async def process_note(
    image: UploadFile,
    codigo_categoria: str = Form(...),
    codigo_usuario: str = Form(...),
    codigo_planilha: str = Form(...),
):
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado.")

    try:
        user = await Usuario.get(codigo_usuario=codigo_usuario)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    
    try:
        category = await Categoria.get(codigo_categoria=codigo_categoria)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    
    try:
        sheet = await Planilha.get(codigo_planilha=codigo_planilha)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planilha não encontrada.")

    url_image_original = upload_to_gcs(image)
    data = execute_scan(image)

    return {
        "valor": data.get("valor_pago"),
        "data": data.get("data_extraida"),
        "url_image_original": url_image_original,
        "url_image_scan": data.get("imagem_url"),
        "codigo_usuario": codigo_usuario,
        "codigo_planilha": codigo_planilha,
        "codigo_categoria": codigo_categoria,
    }

@router.post("/confirm")
async def confirm_note(request: SaveNoteSchema):

    try:
        user = await Usuario.get(codigo_usuario=request.codigo_usuario)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    
    try:
        category = await Categoria.get(codigo_categoria=request.codigo_categoria)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    
    sheet = await Planilha.filter(codigo_planilha=request.codigo_planilha, codigo_usuario=request.codigo_usuario).first()

    if not sheet:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ão encontrei essa planilha para este usuário.")

    try:
        data_formatada = datetime.strptime(request.data, "%d/%m/%Y").date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data inválido. Use DD/MM/YYYY.")

    if not request.url_image_original:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL da imagem original é obrigatória.")

    if not request.url_image_scan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL da imagem digitalizada é obrigatória.")

    valor_float = float(request.valor.replace(",", "."))
    valor_centavos = int(valor_float * 100)

    note = await Nota.create(
        data=data_formatada,
        valor=valor_centavos,
        codigo_categoria=category,
        codigo_usuario=user,
        id_planilha=sheet,
        url_image_original=request.url_image_original,
        url_image_scan=request.url_image_scan,
    )

    return {"id": note.id, "message": "Nota salva com sucesso!"}

@router.post("/reject")
async def reject_note(image_urls: list[str]):
    if not image_urls:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhuma URL de imagem fornecida.")
    
    for image_url in image_urls:
        try:
            exclude_from_gcs(image_url)
        except HTTPException as e:
            raise e

    return {"message": "Imagens rejeitadas e excluídas com sucesso."}