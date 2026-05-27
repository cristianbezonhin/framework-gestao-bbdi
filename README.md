# bbdi-gestao

App de gestao estrategica BBDI. Centraliza metas, projetos e tarefas dos 7 setores (Comercial, SAC, Financeiro, Logistica, Marketing, RMA, RH). Diretor acompanha velocidade de execucao; supervisores gerenciam seu setor.

## Stack
Python 3.11 + FastAPI + SQLite + HTML/Tailwind/Alpine.js + Docker/Coolify.

## Rodar localmente

```bash
cp .env.example .env
# editar .env com SESSION_SECRET, DIRETOR_SENHA, SUPERVISOR_SENHA_DEFAULT

# opcao 1: docker
docker compose up --build

# opcao 2: python local
pip install -r requirements.txt
bash start.sh
```

Abrir `http://localhost:18090`.

## Login
- Diretor: `cristian@bbdi.com.br` + `DIRETOR_SENHA`
- Supervisores: `<setor>@bbdi.com.br` + `SUPERVISOR_SENHA_DEFAULT`
  (setor = comercial, sac, financeiro, logistica, marketing, rma, rh)

## Templates de hierarquia
Cada setor pode usar um dos 3 modelos (diretor configura em `/setor_config`):

| Template | Niveis |
|---|---|
| OKR | Objetivo Anual -> Key Result -> Projeto -> Tarefa |
| Simples | Meta (trimestral/mensal) -> Projeto -> Tarefa |
| Desafios | Desafio -> Meta -> Projeto -> Tarefa |

## Deploy Coolify
1. Push repo no GitHub
2. Coolify -> nova aplicacao Docker, apontar para repo
3. Configurar variaveis: `SESSION_SECRET`, `DIRETOR_SENHA`, `SUPERVISOR_SENHA_DEFAULT`
4. Volume persistente: `/app/data`
5. Porta: 18090
