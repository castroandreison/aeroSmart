from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Aeroclube(Base):
    __tablename__ = "aeroclubes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), unique=True, nullable=False)
    topic_write = Column(String(255), nullable=True)
    topic_read = Column(String(255), nullable=True)
    created_at = Column(DateTime(), server_default=func.now())

    usuarios = relationship("Usuario", back_populates="aeroclube_rel")
