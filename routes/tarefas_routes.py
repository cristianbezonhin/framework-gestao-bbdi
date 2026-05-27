"""CRUD de tarefas."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from auth import escopo_setor_para_user, pode_acessar_setor, require_user
from scripts.projetos_db import get as get_projeto
from scripts.projetos_db import recalcular_progresso
from scripts.tarefas_db import (
    atualizar,
    criar,
    get,
    listar,
    soft_delete,
    trocar_status,
)

router = APIRouter(prefix="/api/tarefas", tags=["tarefas"])


@router.get("")
async def list_tarefas(
    user: dict = Depends(require_user),
    projeto_id: Optional[int] = Query(None),
    setor: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    setor_efetivo = escopo_setor_para_user(user, setor)
    return listar(projeto_id=projeto_id, setor_id=setor_efetivo, status=status)


@router.get("/{tarefa_id}")
async def get_tarefa(tarefa_id: int, user: dict = Depends(require_user)):
    t = get(tarefa_id)
    if not t:
        raise HTTPException(404, "Tarefa nao encontrada")
    if not pode_acessar_setor(user, t["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    return t


@router.post("")
async def create_tarefa(
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    projeto_id = payload.get("projeto_id")
    if not isinstance(projeto_id, int):
        raise HTTPException(400, "projeto_id obrigatorio (int)")
    p = get_projeto(projeto_id)
    if not p:
        raise HTTPException(404, "Projeto inexistente")
    if not pode_acessar_setor(user, p["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    titulo = (payload.get("titulo") or "").strip()
    if not titulo:
        raise HTTPException(400, "titulo obrigatorio")
    tid = criar(
        projeto_id=projeto_id,
        setor_id=p["setor_id"],
        titulo=titulo,
        descricao=payload.get("descricao", ""),
        responsavel_id=payload.get("responsavel_id"),
        prazo=payload.get("prazo"),
        status=payload.get("status", "a_fazer"),
        prioridade=payload.get("prioridade", "media"),
    )
    return get(tid)


@router.patch("/{tarefa_id}")
async def update_tarefa(
    tarefa_id: int,
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    t = get(tarefa_id)
    if not t:
        raise HTTPException(404, "Tarefa nao encontrada")
    if not pode_acessar_setor(user, t["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    if not atualizar(tarefa_id, payload):
        raise HTTPException(400, "Nada para atualizar")
    if "status" in payload:
        recalcular_progresso(t["projeto_id"])
    return get(tarefa_id)


@router.post("/{tarefa_id}/status")
async def set_status(
    tarefa_id: int,
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    t = get(tarefa_id)
    if not t:
        raise HTTPException(404, "Tarefa nao encontrada")
    if not pode_acessar_setor(user, t["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    status = (payload.get("status") or "").strip()
    if not trocar_status(tarefa_id, status):
        raise HTTPException(400, "status invalido")
    recalcular_progresso(t["projeto_id"])
    return get(tarefa_id)


@router.delete("/{tarefa_id}")
async def delete_tarefa(tarefa_id: int, user: dict = Depends(require_user)):
    t = get(tarefa_id)
    if not t:
        raise HTTPException(404, "Tarefa nao encontrada")
    if not pode_acessar_setor(user, t["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    soft_delete(tarefa_id)
    recalcular_progresso(t["projeto_id"])
    return {"ok": True}
