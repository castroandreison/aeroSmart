from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Aeronave(Base):
    __tablename__ = "aeronaves"

    id = Column(Integer, primary_key=True, index=True)
    matricula = Column(String(20), unique=True, nullable=False, index=True)
    modelo = Column(String(100), nullable=False)
    fabricante = Column(String(100), nullable=True)
    tipo = Column(String(100), nullable=True)
    peso_maximo = Column(Float, nullable=True)
    operador = Column(String(255), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    proprietario = relationship("Usuario", back_populates="aeronaves")
    agendamentos = relationship("Agendamento", back_populates="aeronave")
