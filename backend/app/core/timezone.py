from datetime import datetime, timezone, timedelta

# São Paulo timezone (GMT-3)
SAO_PAULO_TZ = timezone(timedelta(hours=-3))

def agora_sp() -> datetime:
    """Retorna datetime atual no timezone de São Paulo (aware)"""
    return datetime.now(SAO_PAULO_TZ)