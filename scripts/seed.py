"""Seed inicial: cria 7 setores e 8 usuarios (diretor + 1 supervisor por setor).

Idempotente: usa INSERT OR IGNORE em setores e NAO sobrescreve senha de usuario existente.
Executado no startup do container (Dockerfile CMD chama `python -m scripts.seed`).
"""
from __future__ import annotations

from config import DIRETOR_SENHA, SESSION_SECRET, SUPERVISOR_SENHA_DEFAULT
from scripts.db import connect, init_db, now_iso
from scripts.usuarios_db import criar as criar_usuario
from scripts.usuarios_db import existe as usuario_existe
from scripts.usuarios_db import hash_senha

SETORES_DEFAULT = [
    {"id": "comercial",  "nome": "Comercial",  "cor": "#0ea5e9", "template": "okr",      "ordem": 1},
    {"id": "sac",        "nome": "SAC",        "cor": "#f59e0b", "template": "simples",  "ordem": 2},
    {"id": "financeiro", "nome": "Financeiro", "cor": "#22c55e", "template": "okr",      "ordem": 3},
    {"id": "logistica",  "nome": "Logistica",  "cor": "#6366f1", "template": "simples",  "ordem": 4},
    {"id": "marketing",  "nome": "Marketing",  "cor": "#a855f7", "template": "desafios", "ordem": 5},
    {"id": "rma",        "nome": "RMA",        "cor": "#ef4444", "template": "simples",  "ordem": 6},
    {"id": "rh",         "nome": "RH",         "cor": "#14b8a6", "template": "desafios", "ordem": 7},
]

DIRETOR = {
    "email": "cristian@bbdi.com.br",
    "nome": "Cristian Bezonhin",
}

SUPERVISORES = [
    {"email": "comercial@bbdi.com.br",  "nome": "Supervisor Comercial",  "setor_id": "comercial"},
    {"email": "sac@bbdi.com.br",        "nome": "Supervisor SAC",        "setor_id": "sac"},
    {"email": "financeiro@bbdi.com.br", "nome": "Supervisor Financeiro", "setor_id": "financeiro"},
    {"email": "logistica@bbdi.com.br",  "nome": "Supervisor Logistica",  "setor_id": "logistica"},
    {"email": "marketing@bbdi.com.br",  "nome": "Supervisor Marketing",  "setor_id": "marketing"},
    {"email": "rma@bbdi.com.br",        "nome": "Supervisor RMA",        "setor_id": "rma"},
    {"email": "rh@bbdi.com.br",         "nome": "Supervisor RH",         "setor_id": "rh"},
]


def upsert_setores() -> int:
    n = 0
    with connect() as conn:
        for s in SETORES_DEFAULT:
            cur = conn.execute(
                """INSERT OR IGNORE INTO setores (id, nome, cor, template, ordem)
                   VALUES (?, ?, ?, ?, ?)""",
                (s["id"], s["nome"], s["cor"], s["template"], s["ordem"]),
            )
            n += cur.rowcount
    return n


def criar_usuarios_iniciais() -> int:
    criados = 0
    if not usuario_existe(DIRETOR["email"]):
        criar_usuario(
            email=DIRETOR["email"],
            nome=DIRETOR["nome"],
            senha_hash=hash_senha(DIRETOR_SENHA, SESSION_SECRET),
            papel="diretor",
            setor_id=None,
        )
        criados += 1
    for s in SUPERVISORES:
        if not usuario_existe(s["email"]):
            criar_usuario(
                email=s["email"],
                nome=s["nome"],
                senha_hash=hash_senha(SUPERVISOR_SENHA_DEFAULT, SESSION_SECRET),
                papel="supervisor",
                setor_id=s["setor_id"],
            )
            criados += 1
    return criados


def run() -> None:
    init_db()
    n_setores = upsert_setores()
    n_users = criar_usuarios_iniciais()
    print(f"[seed] setores adicionados: {n_setores} | usuarios criados: {n_users}")


if __name__ == "__main__":
    run()
