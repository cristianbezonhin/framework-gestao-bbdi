"""Conversao entre periodo (anual/trimestral/mensal + ano/trimestre/mes) e datas inicio/fim."""
from __future__ import annotations

from datetime import date
from typing import Optional


def periodo_para_datas(
    periodo_tipo: str,
    ano: int,
    trimestre: Optional[int] = None,
    mes: Optional[int] = None,
) -> tuple[str, str]:
    """Retorna (data_inicio, data_fim) ISO para um periodo."""
    if periodo_tipo == "anual":
        return f"{ano}-01-01", f"{ano}-12-31"
    if periodo_tipo == "trimestral":
        if trimestre is None or trimestre not in (1, 2, 3, 4):
            return f"{ano}-01-01", f"{ano}-12-31"
        mes_inicio = (trimestre - 1) * 3 + 1
        mes_fim = mes_inicio + 2
        ultimo_dia = _ultimo_dia_mes(ano, mes_fim)
        return f"{ano}-{mes_inicio:02d}-01", f"{ano}-{mes_fim:02d}-{ultimo_dia:02d}"
    if periodo_tipo == "mensal":
        if mes is None or not (1 <= mes <= 12):
            return f"{ano}-01-01", f"{ano}-12-31"
        ultimo_dia = _ultimo_dia_mes(ano, mes)
        return f"{ano}-{mes:02d}-01", f"{ano}-{mes:02d}-{ultimo_dia:02d}"
    return f"{ano}-01-01", f"{ano}-12-31"


def _ultimo_dia_mes(ano: int, mes: int) -> int:
    if mes == 12:
        return 31
    proximo_inicio = date(ano, mes + 1, 1)
    return (proximo_inicio - date(ano, mes, 1)).days


def pct_tempo_decorrido(
    data_inicio: Optional[str], data_fim: Optional[str], hoje: Optional[date] = None
) -> Optional[int]:
    """% do periodo decorrido entre inicio e fim. None se nao da pra calcular."""
    if not data_inicio or not data_fim:
        return None
    try:
        di = date.fromisoformat(data_inicio[:10])
        df = date.fromisoformat(data_fim[:10])
    except ValueError:
        return None
    if hoje is None:
        hoje = date.today()
    total = (df - di).days
    if total <= 0:
        return 100 if hoje >= df else 0
    decorrido = (hoje - di).days
    if decorrido <= 0:
        return 0
    if decorrido >= total:
        return 100
    return round(100 * decorrido / total)
