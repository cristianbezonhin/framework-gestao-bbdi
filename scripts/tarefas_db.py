"""CRUD de tarefas vinculadas a projetos."""
from __future__ import annotations

from typing import Optional

from scripts.db import connect, now_iso, row_to_dict

STATUS_TAREFA = {"a_fazer", "fazendo", "revisao", "feito", "cancelado"}
PRIORIDADES = {"baixa", "media", "alta"}


def listar(
    *,
    projeto_id: Optional[int] = None,
    setor_id: Optional[str] = None,
    status: Optional[str] = None,
    responsavel_id: Optional[int] = None,
    periodo: Optional[str] = None,
) -> list[dict]:
    where = ["deletado_em IS NULL"]
    params: list = []
    if projeto_id is not None:
        where.append("projeto_id = ?")
        params.append(projeto_id)
    if setor_id:
        where.append("setor_id = ?")
        params.append(setor_id)
    if status:
        where.append("status = ?")
        params.append(status)
    if responsavel_id is not None:
        where.append("responsavel_id = ?")
        params.append(responsavel_id)

    # Filtro de periodo (Inbox UX). Sempre exclui feito/cancelado quando filtra.
    if periodo == "hoje":
        where.append("prazo IS NOT NULL AND date(prazo) <= date('now', 'localtime')")
        where.append("status NOT IN ('feito', 'cancelado')")
    elif periodo == "semana":
        where.append("prazo IS NOT NULL AND date(prazo) <= date('now', '+7 days', 'localtime')")
        where.append("status NOT IN ('feito', 'cancelado')")
    elif periodo == "atrasadas":
        where.append("prazo IS NOT NULL AND date(prazo) < date('now', 'localtime')")
        where.append("status NOT IN ('feito', 'cancelado')")
    elif periodo == "feitas":
        where.append("status = 'feito'")
    # "todas" ou None: sem filtro adicional

    sql = f"SELECT * FROM tarefas WHERE {' AND '.join(where)} ORDER BY prazo IS NULL, prazo, id"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [row_to_dict(r) for r in rows]


def get(tarefa_id: int) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM tarefas WHERE id = ? AND deletado_em IS NULL",
            (tarefa_id,),
        ).fetchone()
        return row_to_dict(row)


def criar(
    *,
    projeto_id: int,
    setor_id: str,
    titulo: str,
    descricao: str = "",
    responsavel_id: Optional[int] = None,
    prazo: Optional[str] = None,
    status: str = "a_fazer",
    prioridade: str = "media",
) -> int:
    if status not in STATUS_TAREFA:
        status = "a_fazer"
    if prioridade not in PRIORIDADES:
        prioridade = "media"
    ts = now_iso()
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO tarefas
                (projeto_id, setor_id, titulo, descricao, responsavel_id, prazo,
                 status, prioridade, concluida_em, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
            (projeto_id, setor_id, titulo.strip(), descricao.strip(),
             responsavel_id, prazo, status, prioridade, ts, ts),
        )
        return cur.lastrowid


def atualizar(tarefa_id: int, campos: dict) -> bool:
    permitidos = {"titulo", "descricao", "responsavel_id", "prazo", "status", "prioridade"}
    sets = []
    params: list = []
    for k, v in campos.items():
        if k == "status" and v not in STATUS_TAREFA:
            continue
        if k == "prioridade" and v not in PRIORIDADES:
            continue
        if k in permitidos:
            sets.append(f"{k} = ?")
            params.append(v)
    if not sets:
        return False
    if "status" in campos and campos["status"] == "feito":
        sets.append("concluida_em = ?")
        params.append(now_iso())
    elif "status" in campos and campos["status"] != "feito":
        sets.append("concluida_em = NULL")
    sets.append("atualizado_em = ?")
    params.append(now_iso())
    params.append(tarefa_id)
    with connect() as conn:
        cur = conn.execute(
            f"UPDATE tarefas SET {', '.join(sets)} WHERE id = ? AND deletado_em IS NULL",
            params,
        )
        return cur.rowcount > 0


def trocar_status(tarefa_id: int, status: str) -> bool:
    if status not in STATUS_TAREFA:
        return False
    return atualizar(tarefa_id, {"status": status})


def soft_delete(tarefa_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE tarefas SET deletado_em = ? WHERE id = ? AND deletado_em IS NULL",
            (now_iso(), tarefa_id),
        )
        return cur.rowcount > 0
