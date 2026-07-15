from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional
from datetime import datetime


class UsuarioCreate(BaseModel):
    nome_completo: str
    cpf: str
    crea: Optional[str] = None
    empresa_operador: Optional[str] = None
    aeroclube_id: Optional[int] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: EmailStr
    senha: str
    matricula: Optional[str] = None
    codigo_interno: Optional[str] = None
    observacoes: Optional[str] = None
    nivel_acesso: str = "solicitante"


class UsuarioUpdate(BaseModel):
    nome_completo: Optional[str] = None
    cpf: Optional[str] = None
    crea: Optional[str] = None
    empresa_operador: Optional[str] = None
    aeroclube_id: Optional[int] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[EmailStr] = None
    matricula: Optional[str] = None
    codigo_interno: Optional[str] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None
    nivel_acesso: Optional[str] = None


class UsuarioResponse(BaseModel):
    id: int
    nome_completo: str
    cpf: str
    crea: Optional[str] = None
    empresa_operador: Optional[str] = None
    aeroclube_id: Optional[int] = None
    aeroclube: Optional[str] = None
    telefone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: str
    ativo: bool
    nivel_acesso: str
    matricula: Optional[str] = None
    codigo_interno: Optional[str] = None
    observacoes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsuarioList(BaseModel):
    id: int
    nome_completo: str
    email: str
    aeroclube: Optional[str] = None
    aeroclube_id: Optional[int] = None
    ativo: bool
    nivel_acesso: str
    matricula: Optional[str] = None

    class Config:
        from_attributes = True


class AlterarSenha(BaseModel):
    senha_atual: str
    nova_senha: str
