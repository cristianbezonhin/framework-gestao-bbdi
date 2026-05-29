# Roadmap do Time — bbdi-gestao

> Síntese do diagnóstico de ponta a ponta feito pelo time (research + UX + domínio), com recomendação de foco e plano de sprints.
> Data: 2026-05-28. Base: Sprint 1 em produção + mudanças de UX não commitadas (cascata/drawer).

---

## 1. A tese convergente (os 3 agentes disseram a mesma coisa)

O produto foi pedido para **um diretor enxergar, numa olhada, a velocidade de execução de cada um dos 7 setores**. Os três diagnósticos, por caminhos independentes, apontam o **mesmo buraco**:

| Agente | Como disse |
|---|---|
| **UX** | A visão de panorama por setor existe no backend (`/api/dashboard/diretor` + `velocidade_pct`) mas está **desligada** no app vivo. O diretor cai numa lista plana de tarefas; não há comparação lado a lado dos 7 setores. |
| **Domínio** | O progresso que o diretor vê (`AVG(progresso_pct)` em `resumo_setor`) é **digitado à mão**, não medido. Projeto→Objetivo **não propaga**. Não existe medição de velocidade real (throughput, burndown) — só um snapshot estático. |
| **Research** | As ferramentas que dão certo (Asana, Profit.co, WorkBoard) fazem o progresso **subir sozinho da execução real (rollup) + check-in semanal medido**. Sem isso, "velocidade" vira opinião. A ausência de check-in é o "silent killer" da adoção. |

**Conclusão única:** o diferencial declarado só é honesto se o número for **derivado da execução real**, não auto-reportado — e for **mostrado como panorama/heatmap por setor**. Hoje falham as duas pontas: o cálculo (manual) e a tela (desligada).

---

## 2. Recomendação de foco do 1º sprint (decisão pedida ao time)

> **Foco recomendado: "Velocidade de execução real + Panorama do diretor".**

Não é o foco "polir UX" nem "antecipar PDI" — é fechar a proposta de valor original. Esse foco é o único que os três diagnósticos sustentam ao mesmo tempo, e ele absorve naturalmente os melhores quick wins de UX (a aba Panorama É um ganho de UX) e corrige os bugs de domínio no caminho. PDI permanece fora (decisão do MVP + anti-padrão de acoplar OKR a avaliação, confirmado pela research).

A lógica impacto × esforço:

```
ALTO   | [1] Rollup       [3] Aba Panorama
IMPACTO| projeto→objetivo (diretor)
       | [2] Bugs P0      [4] Check-in semanal
       |
       | [9] meta_valor   [7] Burndown/snapshots
BAIXO  | [8] Quick wins UX soltos
       +----------------------------------------
         BAIXO ESFORÇO            ALTO ESFORÇO
```

---

## 3. Plano — Sprint "Velocidade + Panorama"

Ordenado por dependência. Itens 1→4 são a espinha dorsal; tudo deriva deles.

### P0 — Fecha a proposta de valor
1. **Rollup automático de progresso** Tarefa→Projeto (já existe) → **Objetivo → pai** (não existe). Adicionar `objetivos_db.recalcular_progresso` agregando filhos (ponderado), subindo por `parent_id`. Campo `progresso_modo IN ('auto','manual')` para preservar override do diretor. *(domínio P0.1)*
2. **Corrigir bugs que falseiam o número:**
   - `projetos_db.recalcular_progresso` inclui tarefas `cancelado` no denominador → derruba o % pra sempre. Excluir do denominador. *(domínio bug)*
   - Validar `status` de objetivo (`STATUS_OBJETIVO` incl. `em_risco`) — hoje aceita qualquer string mas a UI/dashboard contam em_risco. *(domínio bug)*
3. **Aba "Panorama" (default do diretor)** consumindo `/api/dashboard/diretor`: 7 setores em cards comparáveis, com a **barra dupla** (progresso × tempo decorrido) agregada por setor + **ranking por quem está mais atrás do ritmo**. Migrar o `grid-setores`/`setor-card` do `diretor_dashboard.html` (morto) para a aba. Default tab por `me.papel`. *(UX #0/#1/#13/#16)*
4. **Check-in semanal leve por setor** — 3 campos (Progresso / Confidence RAG / Bloqueio) com **timestamp** gravado. Esse timestamp ("dias desde o último check-in") é o medidor de velocidade mais barato e honesto. *(research rec.2 + 15Five/Weekdone PPP)*

### P1 — Solidez e velocidade "de verdade"
5. **Throughput por setor**: tarefas concluídas/semana via query sobre `concluida_em` (dado já gravado, nunca consultado). Sparkline de tendência. *(domínio P1 + research rec.6)*
6. **Confidence com nota obrigatória** (evidência, não humor) — mata o "verde otimista". *(research rec.4)*
7. **Tabela `progresso_snapshots`** como infra para burndown/tendência. *(domínio P1.6)*
8. **Ativar `meta_valor`/`valor_atual`** — metas numéricas ("faturar R$2M") deixam de ser medidas como % de tarefas. Distinguir KR-métrica de KR-marco. *(domínio P1.5)*

### P2 — Higiene (junto, baixo custo)
- Erros via `showToast` em vez de `alert()` cru; `confirm()` nativo → mini-modal. *(UX quick win 2)*
- Atalhos de teclado anunciados no FAB: implementar ou remover do tooltip. *(UX 3)*
- Spinner/skeleton ligado à flag `carregando` na troca de filtros/abas. *(UX 4)*
- Modal de criação respeita o template do setor (não jogar os 6 níveis na cara). *(UX 8)*
- Remover código morto (`*_dashboard.html`, `*_detalhe.html`, `setor_config.html` redirecionados) após migrar o útil. *(UX 15)*
- Renomear/remover `velocidade_pct` (rótulo enganoso); robustez da cascata (404 por status HTTP, não string match). *(domínio P2)*

---

## 4. Riscos de migração (do diagnóstico de domínio)

- Itens 1/5/7/8 exigem ALTER/nova tabela — `_alter_idempotente` (`db.py:48`) já cobre. **Baixo risco.**
- **Atenção:** ao ligar a propagação automática (item 1), objetivos com progresso manual legado serão sobrescritos no 1º recálculo. **Mitigar:** marcar os existentes como `manual` na migração + backfill consciente.
- Troca de template de setor já **não** destrói objetivos (correto) — manter; só falta avisar na UI quando há objetivos órfãos de framework divergente.

---

## 5. Anti-padrões a evitar no MVP (research)

- Não acoplar OKR a avaliação/PDI (derruba adoção) — alinhado com PDI na fase 2.
- Não cascatear além de 2 níveis (empresa → setor); nada de OKR individual com 7 setores.
- Limitar a 3–4 objetivos / 2–4 KRs por setor.
- Progresso nunca auto-reportado sem evidência.

---

## 6. Decisões abertas para o diretor

1. **Confidence/RAG no check-in:** automático (derivado de progresso × tempo) ou o supervisor escolhe a cor manualmente a cada semana? (research recomenda manual+nota; mais honesto, mais atrito.)
2. **Cadência do check-in:** semanal é o padrão de mercado. Confirma semanal, ou quinzenal para um time de 8?
3. **Override manual de progresso:** manter a possibilidade de o diretor digitar progresso por cima do rollup automático, ou progresso passa a ser 100% derivado da execução?
4. **Metas numéricas (`meta_valor`):** entram já neste sprint (item 8) ou ficam para o próximo?

---

*Próximo passo (modo de execução definido pelo diretor: "executa e revisa no fim"): com o foco confirmado, o time implementa P0→P1 de forma autônoma e entrega em commit/PR para revisão. P0 itens 1–3 são o caminho crítico.*
