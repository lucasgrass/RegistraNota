from fastapi import APIRouter, HTTPException, status, UploadFile, Form, Query
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import atomic

from app.core.security import validate_access_token
from app.schemas import NoteSchema, UserNotesSchema, SaveNoteSchema, RejectNoteSchema, FilterNotesSchema
from app.models import Nota, Usuario, Categoria, Planilha
from app.services.gcs import upload_to_gcs, exclude_from_gcs, generate_signed_url
from app.services.scan import execute_scan
from datetime import datetime, timedelta

router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("/last")
async def get_last_notes(request: UserNotesSchema):

    codigo_usuario = await validate_access_token(request.access_token)

    user = await Usuario.filter(codigo_usuario=codigo_usuario).exists()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    last_notes = await Nota.filter(codigo_usuario=codigo_usuario).order_by("-created_at").limit(10)

    if not last_notes:
        raise HTTPException(status_code=204, detail="Não há notas para esse usuário.")

    return {
        "notes": last_notes
    }

@router.post("/history")
async def filter_notes(request: FilterNotesSchema):
    codigo_usuario = await validate_access_token(request.access_token)

    user_exists = await Usuario.filter(codigo_usuario=codigo_usuario).exists()
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    try:
        sheet = await Planilha.get(codigo_planilha=request.codigo_planilha, codigo_usuario=codigo_usuario)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planilha não encontrada para este usuário.")

    filters = {
        "codigo_usuario": codigo_usuario,
        "planilha_id": sheet.id
    }

    days = {
        "ultimos_3_dias": 3,
        "ultimos_7_dias": 7,
        "ultimos_14_dias": 14,
        "ultimo_mes": 30,
        "ultimos_3_meses": 90
    }
    
    if request.periodo:
        if request.periodo not in days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Período inválido: {request.periodo}. Opções válidas: {', '.join(days.keys())}."
            )

        start_date = datetime.utcnow() - timedelta(days=days[request.periodo])
        filters["created_at__gte"] = start_date

    notes = await Nota.filter(**filters).order_by("-created_at")

    return {
        "sheet_id": sheet.id,
        "codigo_planilha": request.codigo_planilha,
        "notes": notes or []
    }

@router.post("/signed-url")
async def get_signed_url(
    access_token: str = Form(...),
    blob_name: str = Form(...)
):
    """
    Gera e retorna uma URL assinada para um arquivo no Google Cloud Storage.
    """
    # Valida o token de acesso
    codigo_usuario = await validate_access_token(access_token)

    # Verifica se o usuário existe
    user_exists = await Usuario.filter(codigo_usuario=codigo_usuario).exists()
    if not user_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    try:
        # Gera a URL assinada
        signed_url = generate_signed_url(blob_name)
        return {"signed_url": signed_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar URL assinada: {str(e)}"
        )

@router.post("/count")
async def count_notes(request: UserNotesSchema):

    codigo_usuario = await validate_access_token(request.access_token)

    user = await Usuario.filter(codigo_usuario=codigo_usuario).exists()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    total_notes = await Nota.filter(codigo_usuario=codigo_usuario).count()

    return {"total_notes": total_notes}

@router.post("/process")
async def process_note(
    image: UploadFile, 
    access_token: str = Form(...), 
    codigo_categoria: str = Form(...), 
    codigo_planilha: str = Form(...), 
    descricao: str = Form(...)
    ):

    codigo_usuario = await validate_access_token(access_token)

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
        "descricao": descricao,
        "url_image_original": url_image_original,
        "url_image_scan": data.get("imagem_url"),
        "codigo_usuario": codigo_usuario,
        "codigo_planilha": codigo_planilha,
        "codigo_categoria": codigo_categoria,
    }

@router.post("/confirm")
@atomic()
async def confirm_note(request: SaveNoteSchema):

    codigo_usuario = await validate_access_token(request.access_token)

    try:
        user = await Usuario.get(codigo_usuario=codigo_usuario)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    
    try:
        category = await Categoria.get(codigo_categoria=request.codigo_categoria)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    
    sheet = await Planilha.filter(codigo_planilha=request.codigo_planilha, codigo_usuario=codigo_usuario).first()

    if not sheet:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não encontrei essa planilha para este usuário.")

    try:
        data_formatada = datetime.strptime(request.data, "%d/%m/%Y").date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Formato de data inválido. Use DD/MM/YYYY.")

    if not request.url_image_original:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL da imagem original é obrigatória.")

    if not request.url_image_scan:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL da imagem digitalizada é obrigatória.")

    try:
        valor_float = float(request.valor.replace(",", "."))
        valor_centavos = int(valor_float * 100)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valor inválido.")

    caixa_atual = user.caixa
    if caixa_atual < valor_centavos:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Saldo insuficiente.")


    note = await Nota.create(
        data=data_formatada,
        valor=valor_centavos,
        descricao=request.descricao,
        codigo_categoria=category,
        codigo_usuario=user,
        planilha_id=sheet.id,
        url_image_original=request.url_image_original,
        url_image_scan=request.url_image_scan,
    )

    user.caixa -= valor_centavos
    await user.save()

    return {"message": "Nota salva com sucesso!"}

@router.post("/reject")
async def reject_note(request: RejectNoteSchema):
    # Valida o token
    _ = await validate_access_token(request.access_token)

    for image_url in request.image_urls:
        try:
            exclude_from_gcs(image_url)
        except HTTPException as e:
            raise HTTPException(
                status_code=e.status_code,
                detail=f"Erro ao excluir a imagem {image_url}: {e.detail}"
            )

    return {"message": "Imagens rejeitadas e excluídas com sucesso."}