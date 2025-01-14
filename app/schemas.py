from pydantic import BaseModel

class UserSchema(BaseModel):
    codigo: str
    nome: str
    email: str
    senha: str
    caixa: int
    is_superuser: bool = False

    class Config:
        from_attributes = True

class GetUserByCodigoSchema(BaseModel):
    codigo: str

    class Config:
        from_attributes = True