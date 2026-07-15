from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class Configuracao(Base):
    __tablename__ = "configuracoes"

    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(Text, nullable=True)
    tipo = Column(String(50), default="texto")
    descricao = Column(String(255), nullable=True)
    created_at = Column(DateTime(), server_default=func.now())
    updated_at = Column(DateTime(), onupdate=func.now())

    @classmethod
    def chaves_padrao(cls):
        return {
            "valor_acionamento": {"valor": "50.00", "tipo": "decimal", "descricao": "Valor por acionamento (R$)"},
            "valor_kwh": {"valor": "0.80", "tipo": "decimal", "descricao": "Valor do kWh (R$)"},
            "potencia_instalada_kw": {"valor": "12.0", "tipo": "decimal", "descricao": "Potência instalada (kW)"},
            "tempo_minimo_cobranca_min": {"valor": "30", "tipo": "int", "descricao": "Tempo mínimo de cobrança (minutos)"},
            "tempo_adicional_min": {"valor": "15", "tipo": "int", "descricao": "Tempo adicional (minutos)"},
            "impostos_percentual": {"valor": "0", "tipo": "decimal", "descricao": "Impostos (%)"},
            "taxas_extras": {"valor": "0", "tipo": "decimal", "descricao": "Taxas extras (R$)"},
            "horario_inicio_operacao": {"valor": "06:00", "tipo": "texto", "descricao": "Horário de início das operações"},
            "horario_fim_operacao": {"valor": "22:00", "tipo": "texto", "descricao": "Horário de fim das operações"},
            "editar_ate_minutos_antes": {"valor": "60", "tipo": "int", "descricao": "Permitir edição até X minutos antes"},
            "whatsapp_habilitado": {"valor": "false", "tipo": "booleano", "descricao": "Habilitar WhatsApp"},
            "automacao_habilitada": {"valor": "true", "tipo": "booleano", "descricao": "Habilitar automação"},
            "mqtt_broker_host": {"valor": "localhost", "tipo": "texto", "descricao": "Host do broker MQTT"},
            "mqtt_broker_port": {"valor": "1883", "tipo": "int", "descricao": "Porta do broker MQTT"},
            "mqtt_username": {"valor": "", "tipo": "texto", "descricao": "Usuário MQTT"},
            "mqtt_password": {"valor": "", "tipo": "texto", "descricao": "Senha MQTT"},
            "mqtt_topic_prefix": {"valor": "aeroclube", "tipo": "texto", "descricao": "Prefixo dos tópicos MQTT"},
            "mqtt_timeout_segundos": {"valor": "10", "tipo": "int", "descricao": "Timeout para confirmação MQTT (s)"},
        }
