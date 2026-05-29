"""Check-in semanal por setor."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from auth import escopo_setor_para_user, pode_acessar_setor, require_user
from scripts.checkin_db import CONFIDENCE_VALIDA, criar, listar_por_setor
from scripts.setores_db import get as get_setor

router = APIRouter(prefix="/api/checkins", tags=["checkins"])


@router.get("")
async def list_checkins(
    user: dict = Depends(require_user),
    setor: Optional[str] = Query(None),
):
    setor_efetivo = escopo_setor_para_user(user, setor)
    if not setor_efetivo:
        raise HTTPException(400, "Informe um setor")
    if not pode_acessar_setor(user, setor_efetivo):
        raise HTTPException(403, "Acesso negado")
    return listar_por_setor(setor_efetivo)


@router.post("")
async def create_checkin(
    payload: dict = Body(...),
    user: dict = Depends(require_user),
):
    setor_id = (payload.get("setor_id") or escopo_setor_para_user(user, None) or "").strip()
    if not setor_id:
        raise HTTPException(400, "setor_id obrigatorio")
    if not pode_acessar_setor(user, setor_id):
        raise HTTPException(403, "Acesso negado a este setor")
    if not get_setor(setor_id):
        raise HTTPException(404, "Setor inexistente")
    confidence = (payload.get("confidence") or "").strip()
    if confidence not in CONFIDENCE_VALIDA:
        raise HTTPException(400, "confidence deve ser verde, amarelo ou vermelho")
    nota = (payload.get("nota") or "").strip()
    if not nota:
        raise HTTPException(400, "nota obrigatoria (evidencia do que mudou)")
    cid = criar(
        setor_id=setor_id,
        confidence=confidence,
        nota=nota,
        bloqueio=payload.get("bloqueio", ""),
        usuario_id=user.get("id"),
    )
    return {"id": cid, "setor_id": setor_id, "confidence": confidence}
