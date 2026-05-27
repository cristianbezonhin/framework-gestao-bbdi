"""GET /api/setores, PATCH /api/setores/{id} (so diretor)."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from auth import require_diretor, require_user
from scripts.setores_db import atualizar_template, get, listar

router = APIRouter(prefix="/api/setores", tags=["setores"])


@router.get("")
async def list_setores(user: dict = Depends(require_user)):
    todos = listar()
    if user["papel"] == "diretor":
        return todos
    return [s for s in todos if s["id"] == user.get("setor_id")]


@router.get("/{setor_id}")
async def get_setor_route(setor_id: str, user: dict = Depends(require_user)):
    if user["papel"] != "diretor" and user.get("setor_id") != setor_id:
        raise HTTPException(403, "Acesso negado a este setor")
    s = get(setor_id)
    if not s:
        raise HTTPException(404, "Setor nao encontrado")
    return s


@router.patch("/{setor_id}")
async def update_setor(
    setor_id: str,
    payload: dict = Body(...),
    user: dict = Depends(require_diretor),
):
    template = (payload.get("template") or "").strip().lower()
    if not template:
        raise HTTPException(400, "Campo 'template' obrigatorio")
    ok = atualizar_template(setor_id, template)
    if not ok:
        raise HTTPException(400, "Template invalido ou setor inexistente")
    return get(setor_id)
