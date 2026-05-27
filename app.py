"""FastAPI app principal do bbdi-gestao."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import STATIC_DIR
from routes.auth_routes import router as auth_router
from routes.comentarios_routes import router as comentarios_router
from routes.dashboard_routes import router as dashboard_router
from routes.objetivos_routes import router as objetivos_router
from routes.pages_routes import router as pages_router
from routes.projetos_routes import router as projetos_router
from routes.setores_routes import router as setores_router
from routes.tarefas_routes import router as tarefas_router
from scripts.db import init_db

app = FastAPI(title="BBDI Gestao", version="0.1.0")


@app.on_event("startup")
async def _on_startup():
    init_db()


# APIs
app.include_router(auth_router)
app.include_router(setores_router)
app.include_router(objetivos_router)
app.include_router(projetos_router)
app.include_router(tarefas_router)
app.include_router(comentarios_router)
app.include_router(dashboard_router)

# Paginas HTML
app.include_router(pages_router)

# Arquivos estaticos compartilhados (theme.css, app.js)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
