"""Serve HTML estaticos por rota. Layout single-page com tabs em /app."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse

from auth import usuario_da_request
from config import STATIC_DIR

router = APIRouter(tags=["pages"])


def _redir_login():
    return RedirectResponse(url="/login", status_code=302)


@router.get("/")
async def root(request: Request):
    user = usuario_da_request(request)
    if not user:
        return _redir_login()
    return RedirectResponse(url="/app", status_code=302)


@router.get("/app")
async def app_page(request: Request):
    user = usuario_da_request(request)
    if not user:
        return _redir_login()
    return FileResponse(str(STATIC_DIR / "app.html"))


# Compat: bookmarks antigos redirecionam para /app
@router.get("/diretor")
async def diretor_page(request: Request):
    return RedirectResponse(url="/app", status_code=302)


@router.get("/setor/{setor_id}")
async def setor_page(setor_id: str, request: Request):
    return RedirectResponse(url="/app", status_code=302)


@router.get("/objetivos/{objetivo_id}")
async def objetivo_page(objetivo_id: int, request: Request):
    # No futuro: poderia passar query param pra abrir drawer; por ora redirect simples.
    return RedirectResponse(url="/app", status_code=302)


@router.get("/projetos/{projeto_id}")
async def projeto_page(projeto_id: int, request: Request):
    return RedirectResponse(url="/app", status_code=302)


@router.get("/setor_config")
async def setor_config_page(request: Request):
    return RedirectResponse(url="/app", status_code=302)


@router.get("/health")
async def health():
    return {"ok": True}
