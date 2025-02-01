from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class UserSchema(BaseModel):
    codigo_usuario: str
    nome: str
    email: str
    senha: str
    caixa: str
    is_superuser: bool = False

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    codigo_usuario: str
    senha: str

    class Config:
        from_attributes = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str

    class Config:
        from_attributes = True

class GetUserSchema(BaseModel):
    access_token: str

    class Config:
        from_attributes = True

class AddCashRegisterSchema(BaseModel):
    access_token: str
    add_codigo_usuario: str
    adicionar_caixa: str

    class Config:
        from_attributes = True

class CategorySchema(BaseModel):
    access_token: str
    codigo_categoria: int
    descricao: str

    class Config:
        from_attributes = True

class NoteSchema(BaseModel):
    imagem: str
    data: date
    valor: int
    codigo_categoria: str
    codigo_usuario: str
    codigo_planilha: str

    class Config:
        from_attributes = True

class SaveNoteSchema(BaseModel):
    access_token: str
    data: str
    valor: str
    descricao: str
    codigo_categoria: str
    codigo_planilha: str
    url_image_original: str
    url_image_scan: str

    class Config:
        from_attributes = True

class RejectNoteSchema(BaseModel):
    access_token: str
    image_urls: List[str]

    class Config:
        from_attributes = True

class UserNotesSchema(BaseModel):
    access_token: str

    class Config:
        from_attributes = True

class FilterNotesSchema(BaseModel):
    access_token: str
    codigo_planilha: str
    periodo: Optional[str] = None

    class Config:
        from_attributes = True

class SheetSchema(BaseModel):
    access_token: str
    codigo_planilha: str

    class Config:
        from_attributes = True

class GetSheetSchema(BaseModel):
    access_token: str

    class Config:
        from_attributes = True

class ReportSchema(BaseModel):
    access_token: str
    codigo_planilha: str

    class Config:
        from_attributes = True