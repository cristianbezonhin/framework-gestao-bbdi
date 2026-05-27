"""Auth: cookie de sessao assinado por itsdangerous, dependency p/ proteger rotas.

Replica o padrao do bloco Gestao do projeto Fretes, generalizado para multi-usuario.
"""
from __future__ import annotations

from typing import Optional

import itsdangerous
from fastapi import HTTPException, Request

from config import SESSION_SECRET
from scripts.usuarios_db import get_por_id

COOKIE_NAME = "bbdi_gestao_session"
COOKIE_MAX_AGE = 86400 * 7  # 7 dias
_SIGNER = itsdangerous.TimestampSigner(SESSION_SECRET + "::bbdi-gestao")


def assinar_token(usuario_id: int) -> str:
    return _SIGNER.sign(str(usuario_id)).decode()


def verificar_token(token: str) -> Optional[int]:
    try:
        raw = _SIGNER.unsign(token, max_age=COOKIE_MAX_AGE)
        return int(raw.decode())
    except Exception:
        return None


def usuario_da_request(request: Request) -> Optional[dict]:
    token = request.cookies.get(COOKIE_NAME, "")
    if not token:
        return None
    uid = verificar_token(token)
    if uid is None:
        return None
    user = get_por_id(uid)
    if not user or not user.get("ativo"):
        return None
    return user


def require_user(request: Request) -> dict:
    """Dependency: garante usuario autenticado, senao 401."""
    user = usuario_da_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    return user


def require_diretor(request: Request) -> dict:
    user = require_user(request)
    if user["papel"] != "diretor":
        raise HTTPException(status_code=403, detail="Acesso restrito ao diretor")
    return user


def pode_acessar_setor(user: dict, setor_id: str) -> bool:
    if user["papel"] == "diretor":
        return True
    return user.get("setor_id") == setor_id


def escopo_setor_para_user(user: dict, setor_id: Optional[str]) -> Optional[str]:
    """Retorna o setor_id efetivo para filtros.

    - Diretor: usa o que pediu (ou None p/ todos).
    - Supervisor: forca o setor dele, ignorando query string.
    """
    if user["papel"] == "diretor":
        return setor_id
    return user.get("setor_id")
