"""Check-in semanal por setor: cadencia leve (confidence RAG + nota + bloqueio).

O timestamp do ultimo check-in e o medidor mais barato de "velocidade de execucao"
do setor: quantos dias o setor passou sem reportar movimento.
"""
from __future__ import annotations

from typing import Optional

from scripts.db import connect, now_iso, row_to_dict

CONFIDENCE_VALIDA = {"verde", "amarelo", "vermelho"}


def criar(
    *,
    setor_id: str,
    confidence: str,
    nota: str,
    bloqueio: str = "",
    usuario_id: Optional[int] = None,
) -> int:
    if confidence not in CONFIDENCE_VALIDA:
        raise ValueError("confidence invalida")
    ts = now_iso()
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO checkins
                (setor_id, usuario_id, confidence, nota, bloqueio, criado_em)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (setor_id, usuario_id, confidence, nota.strip(), bloqueio.strip(), ts),
        )
        return cur.lastrowid


def listar_por_setor(setor_id: str, limit: int = 12) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT c.*, u.nome AS usuario_nome
               FROM checkins c
               LEFT JOIN usuarios u ON u.id = c.usuario_id
               WHERE c.setor_id = ?
               ORDER BY c.criado_em DESC
               LIMIT ?""",
            (setor_id, limit),
        ).fetchall()
        return [row_to_dict(r) for r in rows]


def ultimo_por_setor(setor_id: str) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute(
            """SELECT c.*, u.nome AS usuario_nome
               FROM checkins c
               LEFT JOIN usuarios u ON u.id = c.usuario_id
               WHERE c.setor_id = ?
               ORDER BY c.criado_em DESC
               LIMIT 1""",
            (setor_id,),
        ).fetchone()
        return row_to_dict(row)


def ultimos_todos() -> dict[str, dict]:
    """Mapa setor_id -> ultimo check-in (para o panorama do diretor)."""
    with connect() as conn:
        rows = conn.execute(
            """SELECT c.*, u.nome AS usuario_nome
               FROM checkins c
               JOIN (
                 SELECT setor_id, MAX(criado_em) AS ult
                 FROM checkins GROUP BY setor_id
               ) m ON m.setor_id = c.setor_id AND m.ult = c.criado_em
               LEFT JOIN usuarios u ON u.id = c.usuario_id""",
        ).fetchall()
        return {r["setor_id"]: row_to_dict(r) for r in rows}
