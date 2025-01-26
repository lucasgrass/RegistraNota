from pydantic import BaseModel
from datetime import date

class UserSchema(BaseModel):
    codigo_usuario: str
    nome: str
    email: str
    senha: str
    caixa: int
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

class CategorySchema(BaseModel):
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
    data: str
    valor: float
    codigo_categoria: int
    codigo_usuario: int
    codigo_planilha: int
    url_image_original: str
    url_image_scan: str

    class Config:
        from_attributes = True

class UserNotesSchema(BaseModel):
    codigo_usuario: str

    class Config:
        from_attributes = True

class SheetSchema(BaseModel):
    access_token: str
    codigo_planilha: str

    class Config:
        from_attributes = True