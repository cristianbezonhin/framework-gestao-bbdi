# Historico de construcao — bbdi-gestao

Documento de referencia da conversa que originou este projeto. Sessao em 2026-05-27 com Claude Code.

---

## 1. O problema

Cristian (diretor de e-commerce BBDI, 4 lojas VTEX) tinha dificuldade de gestao com o time tatico (7 supervisores: Comercial, SAC, Financeiro, Logistica, Marketing, RMA, RH).

**Sintomas:**
- Falta de clareza e profundidade nos objetivos da empresa para os lideres
- Dificuldade em separar **desafios/metas trimestrais e mensais** de **projetos** de **tarefas**
- Sem visibilidade da velocidade de execucao de cada setor

**Solucao desejada:** um app dentro de um repositorio GitHub que centralize tudo (PDI, metas, projetos, tarefas) e sirva como "mapa geral" da organizacao para diretor e supervisores.

---

## 2. Decisoes da conversa

| Decisao | Escolha |
|---|---|
| Localizacao do codigo | **Novo repositorio GitHub separado** (nao modulo do Fretes) — nome sugerido: `bbdi-gestao` |
| Usuarios MVP | Diretor (Cristian) + 7 supervisores (1 por setor) |
| Hierarquia | **3 templates selecionaveis** por setor pra testar qual funciona melhor: OKR, Simples, Desafios |
| PDI (Plano de Desenvolvimento Individual) | **Fase 2** — MVP foca em metas/projetos/tarefas |
| Stack | Python 3.11 + FastAPI + SQLite + HTML/Tailwind/Alpine.js + Docker/Coolify (mesma do Fretes) |
| Hospedagem | Coolify pessoal (mesmo onde rodam Fretes e Tableau MCP) |
| Porta | 18090 (Fretes usa 18080) |

### Os 3 templates de hierarquia

```
OKR:       Objetivo Anual -> Key Result Trimestral -> Projeto -> Tarefa
Simples:   Meta (trimestral/mensal) -> Projeto -> Tarefa
Desafios:  Desafio Estrategico -> Meta -> Projeto -> Tarefa
```

Cada setor escolhe o seu em `/setor_config`. Trocar template **nao apaga** objetivos antigos — eles ficam marcados com `template_origem` antigo.

### Templates iniciais por setor (chute do seed; diretor ajusta na UI)

| Setor | Cor | Template default |
|---|---|---|
| Comercial | #0ea5e9 | okr |
| SAC | #f59e0b | simples |
| Financeiro | #22c55e | okr |
| Logistica | #6366f1 | simples |
| Marketing | #a855f7 | desafios |
| RMA | #ef4444 | simples |
| RH | #14b8a6 | desafios |

---

## 3. Arquitetura

### Decisao critica: tabela unica de objetivos

Em vez de criar 4 tabelas (`objetivos_anuais`, `key_results`, `metas`, `desafios`), tudo vai numa unica tabela `objetivos` com:
- Campo `nivel` (`objetivo_anual` | `key_result` | `meta` | `desafio`)
- Auto-referencia `parent_id` (pode apontar para outro objetivo)
- Validacao de hierarquia feita na **camada de servico** (`scripts/objetivos_db.py`), nao no schema

Vantagem: um unico CRUD, uma tela, uma rota. Custo: regra de negocio precisa validar `nivel` vs template do setor.

### Estrutura de pastas

```
bbdi-gestao/
├── Dockerfile, docker-compose.yml, requirements.txt, .env.example
├── app.py                  # FastAPI + include_routers + StaticFiles
├── config.py               # carrega .env, define paths e secrets
├── auth.py                 # cookie de sessao com itsdangerous (replica padrao Fretes)
├── routes/
│   ├── auth_routes.py
│   ├── setores_routes.py
│   ├── objetivos_routes.py
│   ├── projetos_routes.py
│   ├── tarefas_routes.py
│   ├── comentarios_routes.py
│   ├── dashboard_routes.py
│   └── pages_routes.py     # serve HTML
├── scripts/
│   ├── db.py               # init_db idempotente + WAL mode
│   ├── seed.py             # 7 setores + 8 usuarios no startup
│   ├── usuarios_db.py
│   ├── setores_db.py
│   ├── objetivos_db.py     # CORACAO: validacao de hierarquia por template
│   ├── projetos_db.py      # inclui recalculo de progresso
│   ├── tarefas_db.py
│   ├── comentarios_db.py
│   └── dashboard_db.py     # queries agregadas
├── data/                   # volume persistente (gestao.db)
└── static/
    ├── login.html
    ├── diretor_dashboard.html
    ├── supervisor_dashboard.html
    ├── objetivo_detalhe.html
    ├── projeto_detalhe.html
    ├── setor_config.html
    └── shared/theme.css, shared/app.js
```

### Modelo de dados (SQLite)

- `setores` — id slug, nome, cor, template, ordem
- `usuarios` — email, senha_hash sha256, papel (diretor/supervisor), setor_id
- `objetivos` — arvore unica com parent_id, nivel, periodo, progresso_pct, status, soft delete
- `projetos` — vinculados a objetivo, com prazo, status, progresso (manual ou recalculado de tarefas)
- `tarefas` — vinculadas a projeto, com responsavel, prazo, status (a_fazer/fazendo/revisao/feito), prioridade
- `comentarios` — polimorficos (entidade_tipo=objetivo/projeto, entidade_id), pra narrativa diretor↔supervisor
- `audit_log` — log leve de acoes

### Multitenancy

- Diretor (`papel=diretor`, `setor_id=NULL`): ve tudo
- Supervisor (`papel=supervisor`, `setor_id=X`): so ve `setor_id=X`
- Helper `escopo_setor_para_user(user, setor_id_pedido)` aplica o filtro

### Calculo automatico de progresso

Quando uma tarefa muda de status, o `routes/tarefas_routes.py` chama `recalcular_progresso(projeto_id)` em `scripts/projetos_db.py`:

```
progresso_pct = round(100 * tarefas_concluidas / tarefas_ativas_totais)
```

Supervisor pode tambem editar `progresso_pct` manualmente (hibrido).

---

## 4. Validacao end-to-end (executada na sessao)

Servidor subiu em `127.0.0.1:18091` (Python 3.9 local). Testes passaram:

| Teste | Resultado |
|---|---|
| `GET /health` | `{"ok":true}` |
| `GET /` sem cookie | 302 -> `/login` |
| `POST /login` diretor | 302 -> `/diretor` + cookie assinado |
| `GET /api/me` | Retorna diretor com setor=null |
| Diretor cria Objetivo Anual no Comercial | id=1, template_origem=okr |
| Diretor cria Key Result filho | id=2 |
| Cria projeto vinculado ao KR | id=1 |
| Cria 3 tarefas | OK |
| Marca 2 de 3 tarefas como feitas | progresso projeto = **67%** automatico |
| Supervisor SAC ve `/api/setores` | so 1 setor (sac) |
| Supervisor SAC tenta `/api/objetivos/1` (Comercial) | **HTTP 403** |
| Supervisor SAC tenta criar no Comercial | **HTTP 403** + `Acesso negado a este setor` |
| Supervisor SAC cria meta no SAC | OK, template_origem=simples |
| Supervisor SAC tenta `/api/dashboard/diretor` | **HTTP 403** |
| Diretor muda template Comercial: okr -> simples | OK |
| Tentar criar `key_result` em setor com template simples | **HTTP 400** `Nivel 'key_result' nao faz parte do template 'simples'` |
| Diretor posta comentario no objetivo 1 | OK + lista correta com nome + papel |

Apos validacao, DB de teste foi removido. Repo pronto pra deploy.

---

## 5. Como rodar

### Local com Docker
```bash
cd ~/bbdi-gestao
cp .env.example .env
# editar .env com SESSION_SECRET (string aleatoria), DIRETOR_SENHA, SUPERVISOR_SENHA_DEFAULT
docker compose up --build
# acessar http://localhost:18090
```

### Local com Python
```bash
cd ~/bbdi-gestao
cp .env.example .env  # editar
pip install -r requirements.txt
bash start.sh
```

### Logins
- Diretor: `cristian@bbdi.com.br` + `DIRETOR_SENHA` (do .env)
- Supervisores: `comercial@bbdi.com.br`, `sac@bbdi.com.br`, `financeiro@bbdi.com.br`, `logistica@bbdi.com.br`, `marketing@bbdi.com.br`, `rma@bbdi.com.br`, `rh@bbdi.com.br` — todos com `SUPERVISOR_SENHA_DEFAULT` (do .env)

---

## 6. Deploy Coolify

1. Subir repo no GitHub:
   ```bash
   cd ~/bbdi-gestao
   git init
   git add .
   git commit -m "Sprint 1 do bbdi-gestao"
   # criar repo no GitHub, depois:
   git remote add origin git@github.com:<user>/bbdi-gestao.git
   git push -u origin main
   ```
2. Coolify -> Nova aplicacao Docker apontando pro repo
3. Variaveis de ambiente:
   - `SESSION_SECRET` — string aleatoria longa
   - `DIRETOR_SENHA` — senha do Cristian
   - `SUPERVISOR_SENHA_DEFAULT` — senha inicial dos supervisores (trocar depois)
4. Volume persistente: `/app/data`
5. Porta: 18090
6. Dominio sugerido: `gestao.bbdi.com.br`

---

## 7. Roadmap (Sprints 2 e 3)

### Sprint 2 — Templates avancados + KPIs reais (3-4 dias)
- Definicao real de "em risco": meta com `progresso_pct < % esperado pelo tempo passado no periodo` (ex: Q2 com 60% do tempo passado, meta em 30% = risco)
- Filtros de periodo com navegacao prev/next via querystring
- Drill-down do diretor com narrativa (ultimos comentarios por setor)
- Validacao de hierarquia tambem na UI (form so mostra niveis aplicaveis)

### Sprint 3 — Polish + Deploy (2-3 dias)
- Audit log com triggers nos `*_db.py`
- Backup diario do SQLite (`sqlite3 .backup`)
- Refinamento visual (badges, indicadores, cores por setor mais consistentes)
- Tela de troca de senha (`POST /api/me/senha`)
- Deploy final em Coolify

### Fase 2 (depois do MVP rodando)
- PDI por supervisor: competencias, feedback 1:1, plano de carreira
- Notificacoes (email/Slack quando meta entra em risco)
- Integracao com Tableau MCP (puxar metricas reais como `progresso_pct`)

---

## 8. Decisoes de design (a guardar)

1. **Hierarquia em tabela unica:** parent_id + nivel + validacao na camada de servico. Mapeamento:
   - okr: `objetivo_anual -> key_result -> projeto -> tarefa`
   - simples: `meta -> projeto -> tarefa`
   - desafios: `desafio -> meta -> projeto -> tarefa`
2. **Auth replica Fretes:** sha256(senha + SESSION_SECRET) + cookie assinado via `itsdangerous.TimestampSigner` (7 dias). Sem cadastro publico.
3. **Sem build de frontend:** Tailwind via CDN, Alpine.js via CDN. Zero npm. Voce edita HTML e ve no browser.
4. **Datas em UTC ISO 8601** no DB; conversao para BR so na UI (`toLocaleString('pt-BR')`).
5. **SQLite WAL mode** ja ligado no `_connect()` para writes concorrentes.
6. **Soft delete em tudo:** coluna `deletado_em`. Queries filtram `WHERE deletado_em IS NULL`. Permite recuperacao manual via SQLite CLI.
7. **Senhas via env var, nunca em codigo.** Seed nao sobrescreve senha de usuario que ja existe (idempotente).

---

## 9. Arquivos chave

| Caminho | O que e |
|---|---|
| `app.py` | Bootstrap FastAPI + include_routers |
| `auth.py` | Login, cookie, dependencies `require_user` / `require_diretor` |
| `scripts/db.py` | Schema SQLite + init_db idempotente |
| `scripts/objetivos_db.py` | **Validacao de hierarquia por template** — coracao da regra de negocio |
| `scripts/seed.py` | 7 setores + 8 usuarios. Roda no startup do container |
| `routes/dashboard_routes.py` | `/api/dashboard/diretor` e `/api/dashboard/setor/{id}` |
| `static/diretor_dashboard.html` | Grid de cards por setor com KPIs |
| `static/supervisor_dashboard.html` | Listas de objetivos do setor + form de criacao |
| `static/setor_config.html` | Diretor escolhe template de cada setor |

---

## 10. Referencias do Fretes que foram aproveitadas

- `Fretes/gestao_routes.py` — padrao de auth com `itsdangerous.TimestampSigner`
- `Fretes/scripts/crm_db.py` — modulo DB com sqlite3 + Lock + init_db idempotente
- `Fretes/Dockerfile` — base (sem Playwright/pandas/OpenAI no novo Dockerfile)
- `Fretes/static/gestao_login.html` — visual do login (paleta amber/slate)
