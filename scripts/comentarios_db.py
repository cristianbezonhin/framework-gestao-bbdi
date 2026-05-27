"""CRUD de comentarios (polimorficos em objetivos e projetos)."""
from __future__ import annotations

from scripts.db import connect, now_iso, row_to_dict

TIPOS_VALIDOS = {"objetivo", "projeto"}


def listar(entidade_tipo: str, entidade_id: int) -> list[dict]:
    if entidade_tipo not in TIPOS_VALIDOS:
        return []
    with connect() as conn:
        rows = conn.execute(
            """SELECT c.*, u.nome AS usuario_nome, u.papel AS usuario_papel
               FROM comentarios c
               LEFT JOIN usuarios u ON u.id = c.usuario_id
               WHERE c.entidade_tipo = ? AND c.entidade_id = ?
               ORDER BY c.criado_em ASC""",
            (entidade_tipo, entidade_id),
        ).fetchall()
        return [row_to_dict(r) for r in rows]


def criar(*, entidade_tipo: str, entidade_id: int, usuario_id: int, texto: str) -> int:
    if entidade_tipo not in TIPOS_VALIDOS:
        raise ValueError(f"entidade_tipo invalido: {entidade_tipo}")
    texto = texto.strip()
    if not texto:
        raise ValueError("texto vazio")
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO comentarios (entidade_tipo, entidade_id, usuario_id, texto, criado_em)
               VALUES (?, ?, ?, ?, ?)""",
            (entidade_tipo, entidade_id, usuario_id, texto, now_iso()),
        )
        return cur.lastrowid


def deletar(comentario_id: int, usuario_id: int, eh_diretor: bool) -> bool:
    """Apaga so se o autor for o usuario ou se for diretor."""
    with connect() as conn:
        if eh_diretor:
            cur = conn.execute("DELETE FROM comentarios WHERE id = ?", (comentario_id,))
        else:
            cur = conn.execute(
                "DELETE FROM comentarios WHERE id = ? AND usuario_id = ?",
                (comentario_id, usuario_id),
            )
        return cur.rowcount > 0
