"""CRUD de setores."""
from __future__ import annotations

from typing import Optional

from scripts.db import connect, row_to_dict
from scripts.objetivos_db import TEMPLATES

TEMPLATES_VALIDOS = set(TEMPLATES.keys())


def listar() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM setores ORDER BY ordem, nome"
        ).fetchall()
        return [row_to_dict(r) for r in rows]


def get(setor_id: str) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM setores WHERE id = ?", (setor_id,)).fetchone()
        return row_to_dict(row)


def atualizar_template(setor_id: str, template: str) -> bool:
    if template not in TEMPLATES_VALIDOS:
        return False
    with connect() as conn:
        cur = conn.execute(
            "UPDATE setores SET template = ? WHERE id = ?",
            (template, setor_id),
        )
        return cur.rowcount > 0
