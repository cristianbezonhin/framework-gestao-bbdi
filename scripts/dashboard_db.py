"""Queries agregadas para dashboards."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from scripts.db import connect, row_to_dict


def _hoje_iso() -> str:
    return date.today().isoformat()


def resumo_setor(setor_id: str, ano: int, trimestre: Optional[int] = None) -> dict:
    hoje = _hoje_iso()
    params_obj = [setor_id, ano]
    sql_obj = """SELECT
                   COUNT(*) AS total,
                   COALESCE(AVG(progresso_pct), 0) AS progresso_medio,
                   SUM(CASE WHEN status = 'concluido' THEN 1 ELSE 0 END) AS concluidos,
                   SUM(CASE WHEN status = 'em_risco' THEN 1 ELSE 0 END) AS em_risco
                 FROM objetivos
                 WHERE setor_id = ? AND periodo_ano = ? AND deletado_em IS NULL"""
    if trimestre is not None:
        sql_obj += " AND (periodo_trimestre = ? OR periodo_trimestre IS NULL)"
        params_obj.append(trimestre)

    params_proj = [setor_id, hoje]
    sql_proj = """SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'concluido' THEN 1 ELSE 0 END) AS concluidos,
                    SUM(CASE WHEN prazo IS NOT NULL AND prazo < ?
                              AND status NOT IN ('concluido', 'cancelado')
                         THEN 1 ELSE 0 END) AS atrasados,
                    COALESCE(AVG(progresso_pct), 0) AS progresso_medio
                  FROM projetos
                  WHERE setor_id = ? AND deletado_em IS NULL"""
    # nota: parametros usados em ordem (?, ?) -> primeiro hoje, depois setor_id
    sql_proj = """SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'concluido' THEN 1 ELSE 0 END) AS concluidos,
                    SUM(CASE WHEN prazo IS NOT NULL AND prazo < ?
                              AND status NOT IN ('concluido', 'cancelado')
                         THEN 1 ELSE 0 END) AS atrasados,
                    COALESCE(AVG(progresso_pct), 0) AS progresso_medio
                  FROM projetos
                  WHERE setor_id = ? AND deletado_em IS NULL"""

    sql_tar = """SELECT
                   COUNT(*) AS total,
                   SUM(CASE WHEN status = 'feito' THEN 1 ELSE 0 END) AS feitas
                 FROM tarefas
                 WHERE setor_id = ? AND deletado_em IS NULL"""

    with connect() as conn:
        obj = conn.execute(sql_obj, params_obj).fetchone()
        proj = conn.execute(sql_proj, (hoje, setor_id)).fetchone()
        tar = conn.execute(sql_tar, (setor_id,)).fetchone()
        return {
            "setor_id": setor_id,
            "objetivos": {
                "total": obj["total"] or 0,
                "concluidos": obj["concluidos"] or 0,
                "em_risco": obj["em_risco"] or 0,
                "progresso_medio": round(obj["progresso_medio"] or 0),
            },
            "projetos": {
                "total": proj["total"] or 0,
                "concluidos": proj["concluidos"] or 0,
                "atrasados": proj["atrasados"] or 0,
                "progresso_medio": round(proj["progresso_medio"] or 0),
            },
            "tarefas": {
                "total": tar["total"] or 0,
                "feitas": tar["feitas"] or 0,
                "velocidade_pct": 0 if not tar["total"] else round(100 * (tar["feitas"] or 0) / tar["total"]),
            },
        }


def panorama_diretor(ano: int, trimestre: Optional[int] = None) -> list[dict]:
    """Retorna resumo por setor para o dashboard do diretor."""
    with connect() as conn:
        setores = conn.execute(
            "SELECT * FROM setores ORDER BY ordem, nome"
        ).fetchall()
    out = []
    for s in setores:
        r = resumo_setor(s["id"], ano, trimestre)
        r["setor"] = row_to_dict(s)
        out.append(r)
    return out


def ultimos_comentarios(setor_id: Optional[str] = None, limit: int = 10) -> list[dict]:
    sql = """SELECT c.*, u.nome AS usuario_nome, u.papel AS usuario_papel
             FROM comentarios c
             LEFT JOIN usuarios u ON u.id = c.usuario_id"""
    params: list = []
    if setor_id:
        # filtro indireto via JOIN nas entidades comentadas
        sql = """SELECT c.*, u.nome AS usuario_nome, u.papel AS usuario_papel,
                        CASE c.entidade_tipo
                          WHEN 'objetivo' THEN o.setor_id
                          WHEN 'projeto'  THEN p.setor_id
                        END AS setor_id_alvo
                 FROM comentarios c
                 LEFT JOIN usuarios u ON u.id = c.usuario_id
                 LEFT JOIN objetivos o ON c.entidade_tipo = 'objetivo' AND o.id = c.entidade_id
                 LEFT JOIN projetos  p ON c.entidade_tipo = 'projeto'  AND p.id = c.entidade_id
                 WHERE
                   (c.entidade_tipo = 'objetivo' AND o.setor_id = ?)
                   OR
                   (c.entidade_tipo = 'projeto'  AND p.setor_id = ?)"""
        params.extend([setor_id, setor_id])
    sql += " ORDER BY c.criado_em DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [row_to_dict(r) for r in rows]
