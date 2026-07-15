from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class NivelAcesso(str, enum.Enum):
    PROPRIETARIO = "proprietario"
    ADMINISTRADOR = "administrador"
    SOLICITANTE = "solicitante"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(255), nullable=False)
    cpf = Column(String(14), unique=True, nullable=False)
    crea = Column(String(50), nullable=True)
    empresa_operador = Column(String(255), nullable=True)
    aeroclube_id = Column(Integer, ForeignKey("aeroclubes.id"), nullable=True)
    telefone = Column(String(20), nullable=True)
    whatsapp = Column(String(20), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)
    nivel_acesso = Column(SAEnum(NivelAcesso), default=NivelAcesso.SOLICITANTE)
    matricula = Column(String(50), unique=True, nullable=True)
    codigo_interno = Column(String(50), unique=True, nullable=True)
    observacoes = Column(Text, nullable=True)
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), onupdate=func.now())
    ultimo_login = Column(DateTime(), nullable=True)

    aeronaves = relationship("Aeronave", back_populates="proprietario", cascade="all, delete-orphan")
    agendamentos = relationship("Agendamento", back_populates="solicitante", cascade="all, delete-orphan")
    aeroclube_rel = relationship("Aeroclube", back_populates="usuarios", lazy="joined")

    @property
    def aeroclube(self):
        return self.aeroclube_rel.nome if self.aeroclube_rel else None
