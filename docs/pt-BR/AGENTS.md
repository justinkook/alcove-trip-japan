# Planejando esta viagem (pt-BR)

Companheiro em português de [`AGENTS.md`](../../AGENTS.md). A versão em inglês na raiz é a lei canônica para agentes. Use este arquivo quando o viajante conversar em português do Brasil.

**Não traduza** chaves YAML, nomes de labels, headings dos Issue templates, nem slash-commands (`/research`, `/experiment`, `/accept-risk`). São contratos de máquina / assist.

`main` é a viagem aceita. Você propõe mudanças. O viajante faz o merge. O chat não é o registro. Nunca edite `main` diretamente e nunca trate seu acordo como decisão.

A raiz do repo é um **scaffold vazio de viagem ao Japão**. Um exemplo completo vive em `examples/japan-summer-2026/` — leia para padrões; copie para a raiz só quando o viajante quiser esse ponto de partida. Hard checks só reforçam schema e limites configurados. `hard_constraints` são defaults opinativos do Japão — retune para a sua viagem.

## Método

Encontre uma opção que satisfaça os requisitos e então tente falsificar de verdade as razões pelas quais ela deveria funcionar.

Um encaixe em requisito é hipótese, não recomendação. Não pare na primeira opção que cabe.

Siga esta ordem. Não pule de uma opção satisfatória para a decisão.

1. Experimento
2. Nova observação
3. Preferências / modelo atualizados
4. Árvore de decisão melhor
5. Pesquisa dirigida
6. Review adversarial
7. Decisão

Você não precisa de sete headings em toda resposta. Precisa passar pelos passos, e toda recomendação deve incluir a falsificação.

### Experimento

Declare uma opção que já atenda requisitos escritos neste repo. Nomeie o requisito que ela diz satisfazer e o registro que mudaria.

Se o requisito não estiver escrito, pergunte. Não invente um para justificar a opção.

### Nova observação

Registre só o que de fato foi aprendido: do viajante, deste repo, ou de uma fonte que você possa apontar.

Rotule cada afirmação: `verified`, `connector-derived`, `repo-derived`, `user-reported`, `inferred` ou `unknown`. Não invente comportamento, gasto ou gosto a partir do itinerário. Unknown continua unknown.

### Preferências / modelo atualizados

Se a observação mudar o que deveria ser verdade da próxima vez, proponha a atualização em uma frase. Não aplique até o viajante aceitar. Não escreva essa lição neste repo. Pessoas, preferências, postmortems e lições entre viagens vivem na camada Alcove; este repo só lista quem está nesta viagem, por id.

### Árvore de decisão melhor

Nomeie a próxima pergunta que mudaria a escolha. Uma pergunta. Dois ramos bastam: se sim, manter; se não, descartar ou substituir.

Se a resposta não mudaria a opção, não pesquise.

### Pesquisa dirigida

Busque só essa pergunta. Cite a fonte. Pare quando estiver respondida ou explicitamente unknown. Não alargue para survey, ranking ou lista de alternativas famosas.

### Review adversarial

Encontre uma opção que satisfaça os requisitos e então tente falsificar as razões pelas quais ela deveria funcionar.

Pergunte qual proxy está trabalhando: nota, prestígio, lista must-see, importância histórica, eficiência, preço ou popularidade. Se a razão cai quando o proxy some, diga.

Um comentário de review é a saída certa quando você vê uma fraqueza mas não tem alternativa concreta. Um pull request é a saída certa quando você pode propor uma mudança internamente consistente. Discordância não bloqueia merge.

### Decisão

O viajante decide. A decisão e o estado que ela muda entram no mesmo commit, em um branch, como pull request. Inclua o que foi escolhido, com o que foi comparado e o motivo. Um PR fechado é proposta rejeitada ou adiada, não apagamento para esconder.

## Hard checks não são este método

Checks determinísticos podem rejeitar estados impossíveis: schema quebrado, horários impossíveis, limite hard configurado, link obrigatório faltando, **ou formas de segredo/PII** (emails, telefones, números parecidos com cartão, chaves de passaporte). Não devem codificar gosto.

**Não faça commit de segredos de identidade ou pagamento.** Coloque emails, telefones, passaportes e similares na memória de sujeito da Alcove (`traveler_ids` opacos neste repo). Ids de confirmação que não são segredos podem viver como `external_ref`.

Se estiver mudando código sob `engine/`, não acrescente substantivos de viagem lá. Nomes de campo vivem em `domains/travel/`.

## Loop de evidência Alcove

A Alcove faz review adversarial de PRs. Preocupações soft viram threads unresolved. Evidência vive como Issues neste repo — não em tabelas Alcove.

| Situação | Ação no GitHub |
| --- | --- |
| Preocupação | Thread de review unresolved no PR |
| Evidência existente | Issue `research` (template `/research`) |
| Evidência nova | Issue `experiment` (template `/experiment`) |
| Aceitar o risco | `/accept-risk` no PR |
| Mudança concreta | Pull request |

Regras:

- Agentes de research/experiment **reportam em Issues**. Preencha Conclusion (e Observation em experiments), depois mova o label de workflow para `resolved`.
- Só o **reviewer Alcove** resolve o thread pai do PR.
- `/research` e `/experiment` mantêm o thread pai **unresolved** até o reviewer reavaliar.
- Nunca auto-merge. Nunca mutar `main` diretamente.
- Os tokens de comando ficam em **inglês** de propósito (contrato do produto).

Idioma dos comentários de review da Alcove: o viajante escolhe no dashboard (**Settings → Review language**), incluindo Português (Brasil).

## Watch (hospedado + agendado no cliente)

1. **Watch hospedado Alcove (Pro)** — ative no dashboard ou MCP (`enable_watch`). Lê `watch.yaml` opcional; abre/atualiza Issue **Alcove watch**. Nunca muta `main`.
2. **Agendado no cliente** — tarefa recorrente no ChatGPT / Claude / Cursor.

Se algo **material** mudar, abra um **pull request** (ou Issue research/experiment). O chat não é o registro.

Vocabulário de labels: `.github/LABELS.md`. Proteção de branch: `docs/branch-protection.md`.
