"""Dashboards agregados (diretor / supervisor)."""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from auth import pode_acessar_setor, require_diretor, require_user
from scripts.dashboard_db import panorama_diretor, resumo_setor, ultimos_comentarios
from scripts.setores_db import get as get_setor

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _ano_padrao() -> int:
    return date.today().year


def _trimestre_atual() -> int:
    m = date.today().month
    return (m - 1) // 3 + 1


@router.get("/diretor")
async def dashboard_diretor(
    user: dict = Depends(require_diretor),
    ano: Optional[int] = Query(None),
    trimestre: Optional[int] = Query(None),
):
    ano = ano or _ano_padrao()
    if trimestre == 0:
        trimestre = None
    return {
        "ano": ano,
        "trimestre": trimestre if trimestre is not None else _trimestre_atual(),
        "por_setor": panorama_diretor(ano, trimestre or _trimestre_atual()),
    }


@router.get("/setor/{setor_id}")
async def dashboard_setor(
    setor_id: str,
    user: dict = Depends(require_user),
    ano: Optional[int] = Query(None),
    trimestre: Optional[int] = Query(None),
):
    if not pode_acessar_setor(user, setor_id):
        raise HTTPException(403, "Acesso negado")
    setor = get_setor(setor_id)
    if not setor:
        raise HTTPException(404, "Setor nao encontrado")
    ano = ano or _ano_padrao()
    tri = trimestre or _trimestre_atual()
    return {
        "setor": setor,
        "ano": ano,
        "trimestre": tri,
        "resumo": resumo_setor(setor_id, ano, tri),
        "ultimos_comentarios": ultimos_comentarios(setor_id, limit=10),
    }
