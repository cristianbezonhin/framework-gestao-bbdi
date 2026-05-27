"""SQLite-backed storage para o app bbdi-gestao.

DB unico em data/gestao.db. init_db idempotente. WAL mode para writes concorrentes.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from config import DB_PATH

_lock = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Context manager publico para uso nos modulos *_db.py."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def init_db() -> None:
    with _lock:
        with _connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS setores (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                cor TEXT DEFAULT '#64748b',
                template TEXT NOT NULL DEFAULT 'simples',
                ordem INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                nome TEXT NOT NULL,
                senha_hash TEXT NOT NULL,
                papel TEXT NOT NULL CHECK (papel IN ('diretor', 'supervisor')),
                setor_id TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (setor_id) REFERENCES setores(id)
            );

            CREATE TABLE IF NOT EXISTS objetivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setor_id TEXT NOT NULL,
                parent_id INTEGER,
                nivel TEXT NOT NULL,
                titulo TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                periodo_tipo TEXT DEFAULT 'trimestral',
                periodo_ano INTEGER NOT NULL,
                periodo_trimestre INTEGER,
                periodo_mes INTEGER,
                meta_valor REAL,
                meta_unidade TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'ativo',
                progresso_pct INTEGER NOT NULL DEFAULT 0,
                responsavel_id INTEGER,
                template_origem TEXT,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                deletado_em TEXT,
                FOREIGN KEY (setor_id) REFERENCES setores(id),
                FOREIGN KEY (parent_id) REFERENCES objetivos(id),
                FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
            );
            CREATE INDEX IF NOT EXISTS idx_obj_setor_periodo
                ON objetivos(setor_id, nivel, periodo_ano, periodo_trimestre);
            CREATE INDEX IF NOT EXISTS idx_obj_parent ON objetivos(parent_id);

            CREATE TABLE IF NOT EXISTS projetos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                objetivo_id INTEGER NOT NULL,
                setor_id TEXT NOT NULL,
                titulo TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'nao_iniciado',
                prazo TEXT,
                progresso_pct INTEGER NOT NULL DEFAULT 0,
                responsavel_id INTEGER,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                deletado_em TEXT,
                FOREIGN KEY (objetivo_id) REFERENCES objetivos(id),
                FOREIGN KEY (setor_id) REFERENCES setores(id),
                FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
            );
            CREATE INDEX IF NOT EXISTS idx_proj_objetivo ON projetos(objetivo_id);
            CREATE INDEX IF NOT EXISTS idx_proj_setor ON projetos(setor_id);

            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                projeto_id INTEGER NOT NULL,
                setor_id TEXT NOT NULL,
                titulo TEXT NOT NULL,
                descricao TEXT DEFAULT '',
                responsavel_id INTEGER,
                prazo TEXT,
                status TEXT NOT NULL DEFAULT 'a_fazer',
                prioridade TEXT NOT NULL DEFAULT 'media',
                concluida_em TEXT,
                criado_em TEXT NOT NULL,
                atualizado_em TEXT NOT NULL,
                deletado_em TEXT,
                FOREIGN KEY (projeto_id) REFERENCES projetos(id),
                FOREIGN KEY (setor_id) REFERENCES setores(id),
                FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
            );
            CREATE INDEX IF NOT EXISTS idx_tar_projeto ON tarefas(projeto_id);
            CREATE INDEX IF NOT EXISTS idx_tar_setor_status ON tarefas(setor_id, status);

            CREATE TABLE IF NOT EXISTS comentarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entidade_tipo TEXT NOT NULL CHECK (entidade_tipo IN ('objetivo', 'projeto')),
                entidade_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                texto TEXT NOT NULL,
                criado_em TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            );
            CREATE INDEX IF NOT EXISTS idx_com_entidade
                ON comentarios(entidade_tipo, entidade_id, criado_em);

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                acao TEXT NOT NULL,
                entidade_tipo TEXT NOT NULL,
                entidade_id INTEGER,
                detalhes_json TEXT,
                criado_em TEXT NOT NULL
            );
            """)


if __name__ == "__main__":
    init_db()
    print(f"DB inicializado em {DB_PATH}")
