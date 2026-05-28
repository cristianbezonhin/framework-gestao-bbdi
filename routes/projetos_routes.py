"""CRUD de projetos."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from auth import escopo_setor_para_user, pode_acessar_setor, require_user
from scripts.objetivos_db import get as get_objetivo
from scripts.periodo import pct_tempo_decorrido, periodo_para_datas
from scripts.projetos_db import (
    atualizar,
    criar,
    get,
    listar,
    recalcular_progresso,
    soft_delete,
)
from scripts.tarefas_db import listar as listar_tarefas

router = APIRouter(prefix="/api/projetos", tags=["projetos"])


def _enriquecer(p: dict) -> dict:
    """Adiciona tempo_decorrido_pct ao dict de projeto."""
    if p:
        p["tempo_decorrido_pct"] = pct_tempo_decorrido(
            p.get("data_inicio"), p.get("data_fim")
        )
    return p


@router.get("")
async def list_projetos(
    user: dict = Depends(require_user),
    setor: Optional[str] = Query(None),
    objetivo_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
):
    setor_efetivo = escopo_setor_para_user(user, setor)
    return [_enriquecer(p) for p in listar(setor_id=setor_efetivo, objetivo_id=objetivo_id, status=status)]


@router.get("/{projeto_id}")
async def get_projeto(projeto_id: int, user: dict = Depends(require_user)):
    p = get(projeto_id)
    if not p:
        raise HTTPException(404, "Projeto nao encontrado")
    if not pode_acessar_setor(user, p["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    p["tarefas"] = listar_tarefas(projeto_id=projeto_id)
    return _enriquecer(p)


@router.post("")
async def create_projeto(
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    objetivo_id = payload.get("objetivo_id")
    if not isinstance(objetivo_id, int):
        raise HTTPException(400, "objetivo_id obrigatorio (int)")
    obj = get_objetivo(objetivo_id)
    if not obj:
        raise HTTPException(404, "Objetivo inexistente")
    if not pode_acessar_setor(user, obj["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    titulo = (payload.get("titulo") or "").strip()
    if not titulo:
        raise HTTPException(400, "titulo obrigatorio")

    # Auto-preenche data_inicio/data_fim a partir do periodo do objetivo pai (se nao vier no payload)
    data_inicio = payload.get("data_inicio")
    data_fim = payload.get("data_fim")
    if not data_inicio or not data_fim:
        if obj.get("periodo_ano"):
            di, df = periodo_para_datas(
                obj.get("periodo_tipo") or "trimestral",
                obj["periodo_ano"],
                obj.get("periodo_trimestre"),
                obj.get("periodo_mes"),
            )
            data_inicio = data_inicio or di
            data_fim = data_fim or df

    pid = criar(
        objetivo_id=objetivo_id,
        setor_id=obj["setor_id"],
        titulo=titulo,
        descricao=payload.get("descricao", ""),
        status=payload.get("status", "nao_iniciado"),
        prazo=payload.get("prazo"),
        data_inicio=data_inicio,
        data_fim=data_fim,
        responsavel_id=payload.get("responsavel_id"),
    )
    return _enriquecer(get(pid))


@router.patch("/{projeto_id}")
async def update_projeto(
    projeto_id: int,
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    p = get(projeto_id)
    if not p:
        raise HTTPException(404, "Projeto nao encontrado")
    if not pode_acessar_setor(user, p["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    if not atualizar(projeto_id, payload):
        raise HTTPException(400, "Nada para atualizar")
    return _enriquecer(get(projeto_id))


@router.post("/{projeto_id}/recalcular")
async def recalcular(projeto_id: int, user: dict = Depends(require_user)):
    p = get(projeto_id)
    if not p:
        raise HTTPException(404, "Projeto nao encontrado")
    if not pode_acessar_setor(user, p["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    pct = recalcular_progresso(projeto_id)
    return {"projeto_id": projeto_id, "progresso_pct": pct}


@router.delete("/{projeto_id}")
async def delete_projeto(projeto_id: int, user: dict = Depends(require_user)):
    p = get(projeto_id)
    if not p:
        raise HTTPException(404, "Projeto nao encontrado")
    if not pode_acessar_setor(user, p["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    soft_delete(projeto_id)
    return {"ok": True}
