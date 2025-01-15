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

class LoginRequest(BaseModel):
    codigo: str
    senha: str

    class Config:
        from_attributes = True

class RefreshTokenRequest(BaseModel):
    refresh_token: str

    class Config:
        from_attributes = True