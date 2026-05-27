"""Serve HTML estaticos por rota. Protege com require_user."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse

from auth import pode_acessar_setor, usuario_da_request
from config import STATIC_DIR

router = APIRouter(tags=["pages"])


def _redir_login():
    return RedirectResponse(url="/login", status_code=302)


@router.get("/")
async def root(request: Request):
    user = usuario_da_request(request)
    if not user:
        return _redir_login()
    if user["papel"] == "diretor":
        return RedirectResponse(url="/diretor", status_code=302)
    return RedirectResponse(url=f"/setor/{user['setor_id']}", status_code=302)


@router.get("/diretor")
async def diretor_page(request: Request):
    user = usuario_da_request(request)
    if not user:
        return _redir_login()
    if user["papel"] != "diretor":
        return RedirectResponse(url=f"/setor/{user['setor_id']}", status_code=302)
    return FileResponse(str(STATIC_DIR / "diretor_dashboard.html"))


@router.get("/setor/{setor_id}")
async def setor_page(setor_id: str, request: Request):
    user = usuario_da_request(request)
    if not user:
        return _redir_login()
    if not pode_acessar_setor(user, setor_id):
        raise HTTPException(403, "Acesso negado a este setor")
    return FileResponse(str(STATIC_DIR / "supervisor_dashboard.html"))


@router.get("/objetivos/{objetivo_id}")
async def objetivo_page(objetivo_id: int, request: Request):
    user = usuario_da_request(request)
    if not user:
        return _redir_login()
    return FileResponse(str(STATIC_DIR / "objetivo_detalhe.html"))


@router.get("/projetos/{projeto_id}")
async def projeto_page(projeto_id: int, request: Request):
    user = usuario_da_request(request)
    if not user:
        return _redir_login()
    return FileResponse(str(STATIC_DIR / "projeto_detalhe.html"))


@router.get("/setor_config")
async def setor_config_page(request: Request):
    user = usuario_da_request(request)
    if not user:
        return _redir_login()
    if user["papel"] != "diretor":
        raise HTTPException(403, "Acesso restrito ao diretor")
    return FileResponse(str(STATIC_DIR / "setor_config.html"))


@router.get("/health")
async def health():
    return {"ok": True}
