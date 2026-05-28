"""CRUD de projetos vinculados a objetivos."""
from __future__ import annotations

from typing import Optional

from scripts.db import connect, now_iso, row_to_dict

STATUS_PROJETO = {"nao_iniciado", "em_andamento", "bloqueado", "concluido", "cancelado"}


def listar(
    *,
    setor_id: Optional[str] = None,
    objetivo_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[dict]:
    where = ["deletado_em IS NULL"]
    params: list = []
    if setor_id:
        where.append("setor_id = ?")
        params.append(setor_id)
    if objetivo_id is not None:
        where.append("objetivo_id = ?")
        params.append(objetivo_id)
    if status:
        where.append("status = ?")
        params.append(status)
    sql = f"SELECT * FROM projetos WHERE {' AND '.join(where)} ORDER BY prazo IS NULL, prazo, id"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [row_to_dict(r) for r in rows]


def get(projeto_id: int) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM projetos WHERE id = ? AND deletado_em IS NULL",
            (projeto_id,),
        ).fetchone()
        return row_to_dict(row)


def criar(
    *,
    objetivo_id: int,
    setor_id: str,
    titulo: str,
    descricao: str = "",
    status: str = "nao_iniciado",
    prazo: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    responsavel_id: Optional[int] = None,
) -> int:
    if status not in STATUS_PROJETO:
        status = "nao_iniciado"
    ts = now_iso()
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO projetos
                (objetivo_id, setor_id, titulo, descricao, status, prazo,
                 data_inicio, data_fim,
                 progresso_pct, responsavel_id, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)""",
            (objetivo_id, setor_id, titulo.strip(), descricao.strip(),
             status, prazo, data_inicio, data_fim, responsavel_id, ts, ts),
        )
        return cur.lastrowid


def atualizar(projeto_id: int, campos: dict) -> bool:
    permitidos = {"titulo", "descricao", "status", "prazo", "data_inicio", "data_fim", "progresso_pct", "responsavel_id"}
    sets = []
    params: list = []
    for k, v in campos.items():
        if k == "status" and v not in STATUS_PROJETO:
            continue
        if k in permitidos:
            sets.append(f"{k} = ?")
            params.append(v)
    if not sets:
        return False
    sets.append("atualizado_em = ?")
    params.append(now_iso())
    params.append(projeto_id)
    with connect() as conn:
        cur = conn.execute(
            f"UPDATE projetos SET {', '.join(sets)} WHERE id = ? AND deletado_em IS NULL",
            params,
        )
        return cur.rowcount > 0


def soft_delete(projeto_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE projetos SET deletado_em = ? WHERE id = ? AND deletado_em IS NULL",
            (now_iso(), projeto_id),
        )
        return cur.rowcount > 0


def recalcular_progresso(projeto_id: int) -> int:
    """Recalcula progresso_pct = tarefas_concluidas / total ativas."""
    with connect() as conn:
        row = conn.execute(
            """SELECT
                 COUNT(*) AS total,
                 SUM(CASE WHEN status = 'feito' THEN 1 ELSE 0 END) AS feitas
               FROM tarefas
               WHERE projeto_id = ? AND deletado_em IS NULL""",
            (projeto_id,),
        ).fetchone()
        total = row["total"] or 0
        feitas = row["feitas"] or 0
        pct = 0 if total == 0 else round(100 * feitas / total)
        conn.execute(
            "UPDATE projetos SET progresso_pct = ?, atualizado_em = ? WHERE id = ?",
            (pct, now_iso(), projeto_id),
        )
        return pct
