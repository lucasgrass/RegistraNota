from fastapi import APIRouter, HTTPException, status, UploadFile, Form
from tortoise.exceptions import DoesNotExist

from app.schemas import NoteSchema, UserNotesSchema, SaveNoteSchema
from app.models import Nota, Usuario, Categoria, Planilha
from app.services.gcs import upload_to_gcs, exclude_of_gcs
from app.services.scan import execute_scan
from app.services.ocr import execute_ocr


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

@router.post("/process")
async def process_note(
    image: UploadFile,
    codigo_categoria: str = Form(...),
    codigo_usuario: str = Form(...),
    codigo_planilha: str = Form(...)
):
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado.")
    
    url_image_original = upload_to_gcs(image)

    # image_scan = execute_scan(url_image_original)
    # url_image_scan = upload_to_gcs(image_scan)

    # data = execute_ocr(url_image_original)

    return {
        # "valor": data.get("valor"),
        # "data": data.get("data"),
        "url_image_original": url_image_original,
        # "url_image_scan": url_image_scan,
        # "codigo_usuario": codigo_usuario,
        # "codigo_planilha": codigo_planilha,
        # "codigo_categoria": codigo_categoria,
    }

@router.post("/confirm")
async def confirm_note(request: SaveNoteSchema):
    note = await Nota.create(
        data=request.data,
        valor=request.valor,
        codigo_categoria=request.codigo_categoria,
        codigo_usuario=request.codigo_usuario,
        codigo_planilha=request.codigo_planilha,
        imagem=request.imagem,
        imagem_original=request.imagem_original,
    )

    return {"id": nota.id, "message": "Nota salva com sucesso!"}

@router.post("/reject")
async def reject_note(image_urls: list):
    if not image_urls:
        raise HTTPException(status_code=400, detail="Nenhuma URL de imagem fornecida.")

    for image_url in image_urls:
        try:
            delete_from_gcs(imagem_url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao excluir imagem do GCS: {str(e)}")

    notes = await Nota.filter(imagem__in=image_urls)
    for note in notes:
        await note.delete()

    return {"message": "Imagens rejeitadas e excluídas com sucesso."}