"""CRUD de objetivos (metas/KRs/desafios)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from auth import escopo_setor_para_user, pode_acessar_setor, require_user
from scripts.objetivos_db import (
    atualizar,
    criar,
    get,
    get_com_filhos,
    listar,
    soft_delete,
    validar_hierarquia_global,
)
from scripts.setores_db import get as get_setor

router = APIRouter(prefix="/api/objetivos", tags=["objetivos"])


@router.get("")
async def list_objetivos(
    user: dict = Depends(require_user),
    setor: Optional[str] = Query(None),
    nivel: Optional[str] = Query(None),
    ano: Optional[int] = Query(None),
    trimestre: Optional[int] = Query(None),
):
    setor_efetivo = escopo_setor_para_user(user, setor)
    return listar(setor_id=setor_efetivo, nivel=nivel, ano=ano, trimestre=trimestre)


@router.get("/{objetivo_id}")
async def get_objetivo(objetivo_id: int, user: dict = Depends(require_user)):
    obj = get_com_filhos(objetivo_id)
    if not obj:
        raise HTTPException(404, "Objetivo nao encontrado")
    if not pode_acessar_setor(user, obj["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    return obj


@router.post("")
async def create_objetivo(
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    setor_id = (payload.get("setor_id") or "").strip()
    if not setor_id:
        raise HTTPException(400, "setor_id obrigatorio")
    if not pode_acessar_setor(user, setor_id):
        raise HTTPException(403, "Acesso negado a este setor")
    setor = get_setor(setor_id)
    if not setor:
        raise HTTPException(404, "Setor inexistente")

    # Os 3 frameworks coexistem em qualquer setor; o "template" do setor agora e apenas preferencia.
    nivel = (payload.get("nivel") or "").strip() or "meta"
    parent_id = payload.get("parent_id")
    parent_nivel = None
    if parent_id is not None:
        parent = get(parent_id)
        if not parent:
            raise HTTPException(400, "parent_id invalido")
        if parent["setor_id"] != setor_id:
            raise HTTPException(400, "parent pertence a outro setor")
        parent_nivel = parent["nivel"]

    erro = validar_hierarquia_global(nivel, parent_nivel)
    if erro:
        raise HTTPException(400, erro)

    titulo = (payload.get("titulo") or "").strip()
    if not titulo:
        raise HTTPException(400, "titulo obrigatorio")
    ano = payload.get("periodo_ano")
    if not isinstance(ano, int):
        raise HTTPException(400, "periodo_ano obrigatorio (int)")

    obj_id = criar(
        setor_id=setor_id,
        nivel=nivel,
        titulo=titulo,
        parent_id=parent_id,
        descricao=payload.get("descricao", ""),
        periodo_tipo=payload.get("periodo_tipo", "trimestral"),
        periodo_ano=ano,
        periodo_trimestre=payload.get("periodo_trimestre"),
        periodo_mes=payload.get("periodo_mes"),
        meta_valor=payload.get("meta_valor"),
        meta_unidade=payload.get("meta_unidade", ""),
        responsavel_id=payload.get("responsavel_id"),
        template_origem=setor["template"],
    )
    return get(obj_id)


@router.patch("/{objetivo_id}")
async def update_objetivo(
    objetivo_id: int,
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    obj = get(objetivo_id)
    if not obj:
        raise HTTPException(404, "Objetivo nao encontrado")
    if not pode_acessar_setor(user, obj["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    if not atualizar(objetivo_id, payload):
        raise HTTPException(400, "Nada para atualizar")
    return get(objetivo_id)


@router.post("/{objetivo_id}/progresso")
async def set_progresso(
    objetivo_id: int,
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    obj = get(objetivo_id)
    if not obj:
        raise HTTPException(404, "Objetivo nao encontrado")
    if not pode_acessar_setor(user, obj["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    pct = payload.get("progresso_pct")
    if not isinstance(pct, int) or not (0 <= pct <= 100):
        raise HTTPException(400, "progresso_pct deve ser int 0-100")
    campos = {"progresso_pct": pct}
    if "status" in payload:
        campos["status"] = payload["status"]
    atualizar(objetivo_id, campos)
    return get(objetivo_id)


@router.delete("/{objetivo_id}")
async def delete_objetivo(objetivo_id: int, user: dict = Depends(require_user)):
    obj = get(objetivo_id)
    if not obj:
        raise HTTPException(404, "Objetivo nao encontrado")
    if not pode_acessar_setor(user, obj["setor_id"]):
        raise HTTPException(403, "Acesso negado")
    soft_delete(objetivo_id)
    return {"ok": True}
