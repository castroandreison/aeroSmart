from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import date, datetime
import io

from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.usuario import Usuario, NivelAcesso
from app.models.aeroclube import Aeroclube
from app.models.agendamento import Agendamento, StatusAgendamento
from app.models.financeiro import Financeiro
from app.models.acionamento import Acionamento
from app.services.financeiro_service import FinanceiroService

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


async def _verificar_token_admin(token: str, session: AsyncSession):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user_id = int(sub)
    result = await session.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.ativo or user.nivel_acesso == NivelAcesso.SOLICITANTE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    return user


def _estilo_tabela(t, colWidths):
    from reportlab.lib import colors
    from reportlab.platypus import TableStyle
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#333333')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#0d0d0d')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#0d0d0d'), colors.HexColor('#1a1a1a')]),
    ]))


def _montar_tabela(dados, cabecalhos, chaves_campos, colWidths):
    from reportlab.platypus import Table
    rows = [cabecalhos]
    for d in dados:
        rows.append([str(d.get(k, "")) for k in chaves_campos])
    t = Table(rows, colWidths=colWidths)
    _estilo_tabela(t, colWidths)
    return t


def gerar_pdf(titulo: str, usuario_nome: str, dados: dict, detalhes: list[dict] = None,
              cabecalhos: list[str] = None, colWidths: list[int] = None, chaves_campos: list[str] = None,
              titulo_tabela: str = "Detalhamento dos Voos",
              detalhes2: list[dict] = None, cabecalhos2: list[str] = None, colWidths2: list[int] = None,
              chaves_campos2: list[str] = None, titulo_tabela2: str = None) -> Response:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.units import mm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=18, textColor=colors.HexColor('#00c6ff'), spaceAfter=4*mm)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.gray, spaceAfter=2*mm)
    normal = styles['Normal']

    elements = []
    elements.append(Paragraph(f"AeroClub - {titulo}", title_style))
    elements.append(Paragraph(f"Usuário: {usuario_nome}", subtitle_style))
    elements.append(Spacer(1, 4*mm))

    resumo_data = [
        ["Indicador", "Valor"],
        ["Voos", str(dados.get("total_voos", 0))],
        ["Horas", f'{dados.get("total_horas", 0)}h'],
        ["Energia", f'{dados.get("total_energia_kwh", 0)} kWh'],
        ["Valor Total", f'R$ {dados.get("total_gasto", 0):.2f}'],
    ]
    t1 = Table(resumo_data, colWidths=[120, 120])
    _estilo_tabela(t1, [120, 120])
    elements.append(t1)
    elements.append(Spacer(1, 6*mm))

    if detalhes:
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#333333')))
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(titulo_tabela, ParagraphStyle('DetailTitle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#00c6ff'))))
        elements.append(Spacer(1, 3*mm))

        _cabecalhos = cabecalhos or ["Data", "Início", "Término", "Aeronave", "Tempo", "Valor"]
        _chaves = chaves_campos or ["data", "hora_inicio", "hora_termino", "aeronave", "tempo", "valor"]
        _widths = colWidths or [70, 55, 55, 70, 50, 60]
        elements.append(_montar_tabela(detalhes, _cabecalhos, _chaves, _widths))

    if detalhes2:
        elements.append(Spacer(1, 4*mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#333333')))
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(titulo_tabela2 or "Detalhamento", ParagraphStyle('DetailTitle2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#00c6ff'))))
        elements.append(Spacer(1, 3*mm))

        _cabecalhos2 = cabecalhos2 or ["Data", "Início", "Término", "Aeronave", "Tempo", "Valor"]
        _chaves2 = chaves_campos2 or ["data", "hora_inicio", "hora_termino", "aeronave", "tempo", "valor"]
        _widths2 = colWidths2 or [70, 55, 55, 70, 50, 60]
        elements.append(_montar_tabela(detalhes2, _cabecalhos2, _chaves2, _widths2))

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ParagraphStyle('Footer', parent=normal, fontSize=7, textColor=colors.gray, alignment=1)))

    doc.build(elements)
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=relatorio_{usuario_nome.replace(' ', '_')}.pdf"},
    )


@router.get("/usuarios/pdf")
async def relatorio_usuario_pdf(
    usuario_nome: str = Query(...),
    data_inicio: str = Query(...),
    data_fim: str = Query(...),
    token: str = Query(...),
    session: AsyncSession = Depends(get_session),
):
    admin = await _verificar_token_admin(token, session)
    user_result = await session.execute(
        select(Usuario).where(Usuario.nome_completo == usuario_nome)
    )
    usuario = user_result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if admin.nivel_acesso == NivelAcesso.SOLICITANTE and admin.id != usuario.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")
    dt_inicio = date.fromisoformat(data_inicio)
    dt_fim = date.fromisoformat(data_fim)

    result = await session.execute(
        select(func.count(Agendamento.id), func.coalesce(func.sum(Acionamento.tempo_ligado_segundos), 0), func.coalesce(func.sum(Financeiro.valor_total), 0), func.coalesce(func.sum(Financeiro.energia_consumida_kwh), 0))
        .outerjoin(Acionamento, Acionamento.agendamento_id == Agendamento.id)
        .outerjoin(Financeiro, Financeiro.agendamento_id == Agendamento.id)
        .where(Agendamento.usuario_id == usuario.id, Agendamento.data >= dt_inicio, Agendamento.data <= dt_fim, Agendamento.status == StatusAgendamento.CONCLUIDO)
    )
    row = result.one()
    dados_resumo = {"usuario_id": usuario.id, "usuario_nome": usuario.nome_completo, "usuario_email": usuario.email, "usuario_matricula": usuario.matricula or "", "periodo_inicio": data_inicio, "periodo_fim": data_fim, "total_voos": row[0] or 0, "total_horas": round((row[1] or 0) / 3600, 2), "total_gasto": float(row[2] or 0), "total_energia_kwh": float(row[3] or 0)}

    detalhes_result = await session.execute(
        select(Agendamento).options(
            selectinload(Agendamento.aeronave),
            selectinload(Agendamento.acionamento),
            selectinload(Agendamento.financeiro),
        )
        .where(Agendamento.usuario_id == usuario.id, Agendamento.data >= dt_inicio, Agendamento.data <= dt_fim, Agendamento.status == StatusAgendamento.CONCLUIDO)
        .order_by(Agendamento.hora_inicio)
    )
    detalhes = []
    for a in list(detalhes_result.scalars().all()):
        tempo_min = round(a.acionamento.tempo_ligado_segundos / 60, 1) if a.acionamento and a.acionamento.tempo_ligado_segundos else 0
        kwh = a.financeiro.energia_consumida_kwh if a.financeiro and a.financeiro.energia_consumida_kwh else 0
        valor = a.financeiro.valor_total if a.financeiro and a.financeiro.valor_total else 0
        detalhes.append({"data": a.data.strftime("%d/%m/%Y"), "hora_inicio": a.hora_inicio.strftime("%H:%M"), "hora_termino": a.hora_termino.strftime("%H:%M"), "aeronave": a.aeronave.matricula if a.aeronave else "-", "tempo": f"{tempo_min} min", "energia": f"{kwh} kWh", "valor": f"R$ {valor:.2f}"})

    return gerar_pdf(f"Relatório do Usuário ({data_inicio} a {data_fim})", usuario.nome_completo, dados_resumo, detalhes,
                     cabecalhos=["Data", "Início", "Término", "Aeronave", "Tempo", "Energia", "Valor"],
                     colWidths=[60, 45, 45, 60, 45, 50, 55],
                     chaves_campos=["data", "hora_inicio", "hora_termino", "aeronave", "tempo", "energia", "valor"],
                     titulo_tabela="Detalhamento dos Voos")


@router.get("/mensal/pdf")
async def relatorio_mensal_pdf(
    ano: int,
    mes: int,
    token: str = Query(...),
    aeroclube: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    admin = await _verificar_token_admin(token, session)
    if admin.nivel_acesso == NivelAcesso.ADMINISTRADOR:
        aeroclube = admin.aeroclube
    from calendar import monthrange
    dt_inicio = date(ano, mes, 1)
    dt_fim = date(ano, mes, monthrange(ano, mes)[1])
    service = FinanceiroService(session)
    resumo = await service.resumo_periodo(dt_inicio, dt_fim, aeroclube=aeroclube)

    uq = select(Usuario.id, Usuario.nome_completo, func.count(Agendamento.id).label("total_voos"), func.coalesce(func.sum(Financeiro.valor_total), 0).label("total_gasto")) \
        .join(Agendamento, Agendamento.usuario_id == Usuario.id) \
        .outerjoin(Financeiro, Financeiro.agendamento_id == Agendamento.id) \
        .where(Agendamento.data >= dt_inicio, Agendamento.data <= dt_fim, Agendamento.status == StatusAgendamento.CONCLUIDO)
    if aeroclube:
        uq = uq.join(Aeroclube, Aeroclube.id == Usuario.aeroclube_id).where(Aeroclube.nome == aeroclube)
    usuarios_result = await session.execute(uq.group_by(Usuario.id, Usuario.nome_completo).order_by(Usuario.nome_completo))
    usuarios_rel = [{"usuario": u.nome_completo, "voos": str(u.total_voos), "gasto": f'R$ {float(u.total_gasto):.2f}'} for u in usuarios_result.all()]

    dq = select(Agendamento).options(
        selectinload(Agendamento.aeronave),
        selectinload(Agendamento.acionamento),
        selectinload(Agendamento.financeiro),
        selectinload(Agendamento.solicitante),
    ).where(Agendamento.data >= dt_inicio, Agendamento.data <= dt_fim, Agendamento.status == StatusAgendamento.CONCLUIDO)
    if aeroclube:
        dq = dq.join(Usuario, Usuario.id == Agendamento.usuario_id).join(Aeroclube, Aeroclube.id == Usuario.aeroclube_id).where(Aeroclube.nome == aeroclube)
    detalhes_result = await session.execute(dq.order_by(Agendamento.data, Agendamento.hora_inicio))
    detalhes = []
    total_kwh = 0
    total_valor = 0
    for a in list(detalhes_result.scalars().all()):
        tempo_min = round(a.acionamento.tempo_ligado_segundos / 60, 1) if a.acionamento and a.acionamento.tempo_ligado_segundos else 0
        kwh = a.financeiro.energia_consumida_kwh if a.financeiro and a.financeiro.energia_consumida_kwh else 0
        valor = a.financeiro.valor_total if a.financeiro and a.financeiro.valor_total else 0
        detalhes.append({
            "data": a.data.strftime("%d/%m/%Y"),
            "hora_inicio": a.hora_inicio.strftime("%H:%M"),
            "hora_termino": a.hora_termino.strftime("%H:%M"),
            "aeronave": a.aeronave.matricula if a.aeronave else "-",
            "tempo": f"{tempo_min} min",
            "energia": f"{kwh} kWh",
            "valor": f"R$ {valor:.2f}",
        })
        total_kwh += kwh
        total_valor += valor

    if detalhes:
        detalhes.append({
            "data": "TOTAL",
            "hora_inicio": "",
            "hora_termino": "",
            "aeronave": "",
            "tempo": "",
            "energia": f"{total_kwh:.1f} kWh",
            "valor": f"R$ {total_valor:.2f}",
        })

    titulo = f"Relatório Mensal ({mes:02d}/{ano})"
    if aeroclube:
        titulo += f" - {aeroclube}"
    return gerar_pdf(titulo, "Administrador", resumo, usuarios_rel,
                     cabecalhos=["Usuário", "Voos", "Valor Gasto"],
                     colWidths=[200, 80, 150],
                     chaves_campos=["usuario", "voos", "gasto"],
                     titulo_tabela="Voos por Usuário",
                     detalhes2=detalhes,
                     cabecalhos2=["Data", "Início", "Término", "Aeronave", "Tempo", "Energia", "Valor"],
                     colWidths2=[55, 42, 42, 55, 42, 50, 55],
                     chaves_campos2=["data", "hora_inicio", "hora_termino", "aeronave", "tempo", "energia", "valor"],
                     titulo_tabela2="Detalhamento dos Voos")
