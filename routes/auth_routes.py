"""Login / logout / /api/me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from auth import (
    COOKIE_MAX_AGE,
    COOKIE_NAME,
    assinar_token,
    require_user,
    usuario_da_request,
)
from config import SESSION_SECRET, STATIC_DIR
from scripts.setores_db import get as get_setor
from scripts.usuarios_db import verificar_senha

router = APIRouter(tags=["auth"])


@router.get("/login")
async def login_page(request: Request):
    if usuario_da_request(request):
        return RedirectResponse(url="/", status_code=302)
    return FileResponse(str(STATIC_DIR / "login.html"))


@router.post("/login")
async def login_submit(email: str = Form(...), senha: str = Form(...)):
    user = verificar_senha(email, senha, SESSION_SECRET)
    if not user:
        return RedirectResponse(url="/login?error=1", status_code=302)
    token = assinar_token(user["id"])
    destino = "/diretor" if user["papel"] == "diretor" else f"/setor/{user['setor_id']}"
    resp = RedirectResponse(url=destino, status_code=302)
    resp.set_cookie(
        COOKIE_NAME, token,
        httponly=True, max_age=COOKIE_MAX_AGE, samesite="lax",
    )
    return resp


@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie(COOKIE_NAME)
    return resp


@router.get("/api/me")
async def me(user: dict = Depends(require_user)):
    setor = get_setor(user["setor_id"]) if user.get("setor_id") else None
    return JSONResponse({
        "id": user["id"],
        "email": user["email"],
        "nome": user["nome"],
        "papel": user["papel"],
        "setor_id": user.get("setor_id"),
        "setor": setor,
    })
