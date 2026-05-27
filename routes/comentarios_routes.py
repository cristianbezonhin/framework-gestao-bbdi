"""CRUD de comentarios."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from auth import pode_acessar_setor, require_user
from scripts.comentarios_db import criar, deletar, listar
from scripts.objetivos_db import get as get_objetivo
from scripts.projetos_db import get as get_projeto

router = APIRouter(prefix="/api/comentarios", tags=["comentarios"])


def _setor_da_entidade(entidade_tipo: str, entidade_id: int) -> str | None:
    if entidade_tipo == "objetivo":
        o = get_objetivo(entidade_id)
        return o["setor_id"] if o else None
    if entidade_tipo == "projeto":
        p = get_projeto(entidade_id)
        return p["setor_id"] if p else None
    return None


@router.get("")
async def list_comentarios(
    entidade_tipo: str = Query(...),
    entidade_id: int = Query(...),
    user: dict = Depends(require_user),
):
    setor = _setor_da_entidade(entidade_tipo, entidade_id)
    if not setor:
        raise HTTPException(404, "Entidade nao encontrada")
    if not pode_acessar_setor(user, setor):
        raise HTTPException(403, "Acesso negado")
    return listar(entidade_tipo, entidade_id)


@router.post("")
async def create_comentario(
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    entidade_tipo = (payload.get("entidade_tipo") or "").strip()
    entidade_id = payload.get("entidade_id")
    texto = (payload.get("texto") or "").strip()
    if not entidade_tipo or not isinstance(entidade_id, int) or not texto:
        raise HTTPException(400, "entidade_tipo, entidade_id e texto sao obrigatorios")
    setor = _setor_da_entidade(entidade_tipo, entidade_id)
    if not setor:
        raise HTTPException(404, "Entidade nao encontrada")
    if not pode_acessar_setor(user, setor):
        raise HTTPException(403, "Acesso negado")
    try:
        cid = criar(
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            usuario_id=user["id"],
            texto=texto,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": cid, "ok": True}


@router.delete("/{comentario_id}")
async def delete_comentario(comentario_id: int, user: dict = Depends(require_user)):
    ok = deletar(comentario_id, user["id"], user["papel"] == "diretor")
    if not ok:
        raise HTTPException(404, "Comentario nao encontrado ou sem permissao")
    return {"ok": True}
