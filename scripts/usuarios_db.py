"""CRUD de usuarios + verificacao de senha."""
from __future__ import annotations

import hashlib
import secrets
from typing import Optional

from scripts.db import connect, now_iso, row_to_dict


def hash_senha(senha: str, salt: str) -> str:
    """sha256(senha + salt). salt e o SESSION_SECRET para evitar rainbow tables."""
    return hashlib.sha256((senha + "::" + salt).encode()).hexdigest()


def get_por_email(email: str) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE email = ? AND ativo = 1",
            (email.lower().strip(),),
        ).fetchone()
        return row_to_dict(row)


def get_por_id(usuario_id: int) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return row_to_dict(row)


def listar() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM usuarios WHERE ativo = 1 ORDER BY papel, nome"
        ).fetchall()
        return [row_to_dict(r) for r in rows]


def criar(
    *,
    email: str,
    nome: str,
    senha_hash: str,
    papel: str,
    setor_id: Optional[str],
) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO usuarios (email, nome, senha_hash, papel, setor_id, ativo, criado_em)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (email.lower().strip(), nome, senha_hash, papel, setor_id, now_iso()),
        )
        return cur.lastrowid


def existe(email: str) -> bool:
    return get_por_email(email) is not None


def verificar_senha(email: str, senha: str, salt: str) -> Optional[dict]:
    """Retorna o usuario se senha confere, senao None."""
    user = get_por_email(email)
    if not user:
        return None
    esperado = hash_senha(senha, salt)
    if secrets.compare_digest(user["senha_hash"], esperado):
        return user
    return None


def atualizar_senha(usuario_id: int, senha_hash: str) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE usuarios SET senha_hash = ? WHERE id = ?",
            (senha_hash, usuario_id),
        )
        return cur.rowcount > 0
