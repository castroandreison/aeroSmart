from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    email: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario_id: int
    nome: str
    email: str
    nivel_acesso: str
    aeroclube_id: Optional[int] = None


class RecuperarSenhaRequest(BaseModel):
    email: str


class RedefinirSenhaRequest(BaseModel):
    token: str
    nova_senha: str
