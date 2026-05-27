"""CRUD de objetivos (arvore unica com nivel + parent_id).

Niveis possiveis: objetivo_anual | key_result | meta | desafio.
Os 3 frameworks (OKR, Simples, Desafios) podem coexistir em qualquer setor.
A validacao de hierarquia e global (estrutural), nao depende do template do setor.
"""
from __future__ import annotations

from typing import Optional

from scripts.db import connect, now_iso, row_to_dict

# Mapeamento template -> cadeia de niveis (mantido como documentacao/preferencia padrao)
TEMPLATES = {
    "okr": ["objetivo_anual", "key_result"],
    "simples": ["meta"],
    "desafios": ["desafio", "meta"],
}

NIVEIS_VALIDOS = {"objetivo_anual", "key_result", "meta", "desafio"}

# Niveis que podem ser criados no topo (sem parent_id), agora em qualquer setor.
NIVEIS_TOPO_PERMITIDOS = {"objetivo_anual", "meta", "desafio"}

# Relacao filho -> parent_nivel obrigatorio.
# Niveis ausentes daqui sao "topo" (parent_nivel deve ser None).
PARENT_OBRIGATORIO = {
    "key_result": "objetivo_anual",
    "meta": "desafio",  # quando dentro do framework Desafios; ou pode ser topo (no Simples)
}


def niveis_do_template(template: str) -> list[str]:
    return TEMPLATES.get(template, ["meta"])


def nivel_topo(template: str) -> str:
    return niveis_do_template(template)[0]


def validar_hierarquia_global(nivel: str, parent_nivel: Optional[str]) -> Optional[str]:
    """Validacao estrutural independente do template do setor.

    Regras:
    - objetivo_anual: sempre topo (parent_nivel deve ser None)
    - desafio:        sempre topo
    - meta:           pode ser topo (framework Simples) OU filha de desafio (framework Desafios)
    - key_result:     deve ter parent objetivo_anual (framework OKR)
    """
    if nivel not in NIVEIS_VALIDOS:
        return f"Nivel '{nivel}' invalido."

    if nivel == "objetivo_anual":
        if parent_nivel is not None:
            return "Objetivo Anual nao pode ter parent."
        return None

    if nivel == "desafio":
        if parent_nivel is not None:
            return "Desafio nao pode ter parent."
        return None

    if nivel == "meta":
        if parent_nivel is None:
            return None  # topo no framework Simples
        if parent_nivel != "desafio":
            return "Meta dentro de hierarquia precisa ser filha de Desafio."
        return None

    if nivel == "key_result":
        if parent_nivel != "objetivo_anual":
            return "Key Result precisa ser filho de Objetivo Anual."
        return None

    return f"Nivel '{nivel}' nao reconhecido."


# Compat: alguns lugares ainda chamam validar_hierarquia(template, nivel, parent_nivel)
def validar_hierarquia(template: str, nivel: str, parent_nivel: Optional[str]) -> Optional[str]:
    """Compat: ignora template, delega para validacao global."""
    return validar_hierarquia_global(nivel, parent_nivel)


def listar(
    *,
    setor_id: Optional[str] = None,
    nivel: Optional[str] = None,
    ano: Optional[int] = None,
    trimestre: Optional[int] = None,
    incluir_deletados: bool = False,
) -> list[dict]:
    where = []
    params: list = []
    if not incluir_deletados:
        where.append("deletado_em IS NULL")
    if setor_id:
        where.append("setor_id = ?")
        params.append(setor_id)
    if nivel:
        where.append("nivel = ?")
        params.append(nivel)
    if ano is not None:
        where.append("periodo_ano = ?")
        params.append(ano)
    if trimestre is not None:
        where.append("periodo_trimestre = ?")
        params.append(trimestre)
    sql = "SELECT * FROM objetivos"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY periodo_ano DESC, periodo_trimestre, id"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [row_to_dict(r) for r in rows]


def get(objetivo_id: int) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM objetivos WHERE id = ? AND deletado_em IS NULL",
            (objetivo_id,),
        ).fetchone()
        return row_to_dict(row)


def get_com_filhos(objetivo_id: int) -> Optional[dict]:
    """Retorna o objetivo com filhos aninhados ate o nivel mais baixo + projetos."""
    obj = get(objetivo_id)
    if not obj:
        return None
    obj["filhos"] = []
    with connect() as conn:
        filhos = conn.execute(
            "SELECT * FROM objetivos WHERE parent_id = ? AND deletado_em IS NULL ORDER BY id",
            (objetivo_id,),
        ).fetchall()
        for f in filhos:
            f_dict = row_to_dict(f)
            # recursivo (raso, 1-2 niveis no max)
            f_dict["filhos"] = []
            netos = conn.execute(
                "SELECT * FROM objetivos WHERE parent_id = ? AND deletado_em IS NULL ORDER BY id",
                (f["id"],),
            ).fetchall()
            f_dict["filhos"] = [row_to_dict(n) for n in netos]
            obj["filhos"].append(f_dict)
    return obj


def criar(
    *,
    setor_id: str,
    nivel: str,
    titulo: str,
    parent_id: Optional[int] = None,
    descricao: str = "",
    periodo_tipo: str = "trimestral",
    periodo_ano: int,
    periodo_trimestre: Optional[int] = None,
    periodo_mes: Optional[int] = None,
    meta_valor: Optional[float] = None,
    meta_unidade: str = "",
    responsavel_id: Optional[int] = None,
    template_origem: Optional[str] = None,
) -> int:
    ts = now_iso()
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO objetivos
                (setor_id, parent_id, nivel, titulo, descricao,
                 periodo_tipo, periodo_ano, periodo_trimestre, periodo_mes,
                 meta_valor, meta_unidade, status, progresso_pct, responsavel_id,
                 template_origem, criado_em, atualizado_em)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ativo', 0, ?, ?, ?, ?)""",
            (setor_id, parent_id, nivel, titulo.strip(), descricao.strip(),
             periodo_tipo, periodo_ano, periodo_trimestre, periodo_mes,
             meta_valor, meta_unidade, responsavel_id,
             template_origem, ts, ts),
        )
        return cur.lastrowid


def atualizar(objetivo_id: int, campos: dict) -> bool:
    permitidos = {
        "titulo", "descricao", "periodo_tipo", "periodo_ano", "periodo_trimestre",
        "periodo_mes", "meta_valor", "meta_unidade", "status", "progresso_pct",
        "responsavel_id",
    }
    sets = []
    params: list = []
    for k, v in campos.items():
        if k in permitidos:
            sets.append(f"{k} = ?")
            params.append(v)
    if not sets:
        return False
    sets.append("atualizado_em = ?")
    params.append(now_iso())
    params.append(objetivo_id)
    with connect() as conn:
        cur = conn.execute(
            f"UPDATE objetivos SET {', '.join(sets)} WHERE id = ? AND deletado_em IS NULL",
            params,
        )
        return cur.rowcount > 0


def soft_delete(objetivo_id: int) -> bool:
    with connect() as conn:
        cur = conn.execute(
            "UPDATE objetivos SET deletado_em = ? WHERE id = ? AND deletado_em IS NULL",
            (now_iso(), objetivo_id),
        )
        return cur.rowcount > 0
