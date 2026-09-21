# Alcove trip starter — Japão (pt-BR)

Scaffold vazio de viagem ao Japão para planejamento no GitHub. Faça o fork, preencha, planeje via ChatGPT / Claude / Cursor. O CI em `main` permanece verde no scaffold vazio.

A lei canônica do agente em inglês continua em [`AGENTS.md`](../../AGENTS.md) na raiz. Use este guia em português quando o viajante conversar em pt-BR. **Chaves YAML, títulos de Issue template e slash-commands (`/research`, `/experiment`) permanecem em inglês** — são contratos de máquina.

Um itinerário de **exemplo** completo fica em [`examples/japan-summer-2026/`](../../examples/japan-summer-2026/).

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 -m engine.facts
python3 -m engine.check
```

## Torne o fork seu

1. Substitua `traveler_ids`, datas e título em `trip.yaml`.
2. Adicione nós em `itinerary/`, `bookings/`, `dependencies/` (ou copie do exemplo).
3. Ajuste `hard_constraints` se os defaults do Japão não couberem.
4. Abra PRs para mudanças — o chat não é o registro.

Siga [`AGENTS.md`](../../AGENTS.md) (ou a versão pt-BR em [`AGENTS.md`](./AGENTS.md) para explicações ao viajante).

## Review Alcove

Instale o GitHub App da Alcove no fork para review adversarial de PRs. Findings soft ficam como threads unresolved; o check `decision-review` roda junto do workflow `check`. Proteja `main` conforme [`docs/branch-protection.md`](../branch-protection.md).

No dashboard Alcove (**Settings → Review language**) você pode pedir comentários de review em **Português (Brasil)**. Os comandos `/research`, `/experiment` e `/accept-risk` continuam em inglês de propósito.

## Watch (hospedado + agendado no cliente)

- **Hospedado (Pro)** — ative watch no repo vinculado na Alcove. Opcional: [`watch.yaml`](../../watch.yaml) na raiz.
- **Agendado no cliente** — tarefa recorrente no ChatGPT / Claude / Cursor permanece válida.

Se algo material mudar, abra um PR (ou Issue de research/experiment). Detalhes: [`AGENTS.md`](./AGENTS.md).
