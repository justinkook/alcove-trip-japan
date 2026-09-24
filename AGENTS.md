# Planning this trip

This file is the instruction set for Cursor, Claude, and ChatGPT while a person is planning in this repository.

`main` is the accepted trip. You propose changes. The traveler merges them. Chat is not the record. Never edit `main` directly, and never treat your agreement as a decision.

New trips start with **structure and checks, without sample travel records**. Keep required files and keys. `null` means unknown or unset, and empty lists contain no accepted choices. Replace the placeholder id and title as the trip takes shape. Add only facts the traveler provides or accepts; do not fill blanks with an invented route, traveler id, budget, or personal limit. Use `domains/travel/schemas/` for record shapes. Test fixtures are synthetic inputs, never planning evidence.

Hard checks enforce schema and configured limits only. Set `hard_constraints` only when the traveler accepts a true hard limit; a soft preference stays a review concern. Passing checks with unset values does not establish that the trip is complete, safe, or booked.

## Method

Find an option that satisfies the requirements, then seriously attempt to falsify the reasons it should work.

A requirement-fit is a hypothesis, not a recommendation. Do not stop at the first option that fits.

Move in this order. Do not skip from a satisfying option to a decision.

1. Experiment
2. New observation
3. Updated preferences / model
4. Better decision tree
5. Targeted research
6. Adversarial review
7. Decision

You do not need seven headings in every reply. You do need to pass through the steps, and every recommendation must include the falsification.

### Experiment

State one option that meets requirements already written in this repo. Name the requirement it claims to satisfy, and the record it would change.

If the requirement is not written down, ask for it. Do not invent one to make an option look justified.

### New observation

Record only what was actually learned: from the traveler, from this repo, or from a source you can point to.

Label each claim: verified, connector-derived, repo-derived, user-reported, inferred, or unknown. Do not invent behavior, spend, or taste from the itinerary. Unknown stays unknown.

### Updated preferences / model

If the observation changes what should be true next time, propose the update in one sentence. Do not apply it until the traveler accepts it. Do not write that lesson into this repo. The people, their preferences, postmortems, and cross-trip lessons live in the agent layer so the next journey can use them without copying a profile into git. This repo only lists who is on this trip, by id. It keeps the trip: what was planned, what was booked, and what actually happened on these dates if someone explicitly records it. A party of two does not automatically impose that pair's constraints on a later solo trip.

### Better decision tree

Name the next question that would change the choice. One question. Two branches are enough: if yes, keep the option; if no, drop or replace it.

If the answer would not change the option, do not research it.

### Targeted research

Look up only that question. Cite the source. Stop when it is answered or explicitly unknown. Do not widen into a survey, a ranking, or a list of famous alternatives.

### Adversarial review

Find an option that satisfies the requirements, then seriously attempt to falsify the reasons it should work.

Ask which proxy is doing the work: rating, prestige, a must-see list, historical importance, efficiency, price, or popularity. If the reason collapses once that proxy is removed, say so.

Challenge the assumptions behind a planned activity: operating conditions, timing, preparation, and fallback value. Do not turn an unverified concern into a hard rule. An early start relative to the traveler's usual departure is review context unless a configured hard limit is violated.

A review comment is the right output when you can see a weakness but cannot offer a concrete alternative. A pull request is the right output when you can propose a change that is internally consistent. Disagreement does not block merge.

### Decision

The traveler decides. The decision and the state it changes land in the same commit, on a branch, as a pull request. Include what was chosen, what it was compared with, and the reason. A closed pull request is a rejected or deferred proposal, not a deletion to hide.

## Hard checks are not this method

Deterministic checks may reject impossible states: broken schema, impossible times, a configured hard limit, a missing required link, **or secret/PII shapes in repo files** (emails, phones, card-like numbers, passport keys). They must not encode taste. Walking distance and weather sensitivity are facts unless a hard limit is set. A planning budget total is not a hard cap. Set the budget currency before enforcing a hard cap.

**Do not commit identity or payment secrets.** Put traveler emails, phones, passport details, and similar in Alcove subject memory (opaque `traveler_ids` in this repo only). Confirmation *ids* that are not secrets may live as `external_ref`; full confirmation codes and card data must not.

If you are changing code under `engine/`, do not add trip words there. Field names live in `domains/travel/`.

## Alcove evidence loop

Alcove adversarially reviews PRs. Soft concerns land as unresolved review threads. Evidence lives as GitHub Issues in this repo — not in Alcove tables. Use the planning method above to decide what to try; use this table for where the work goes.

| Situation | GitHub action |
| --- | --- |
| Concern | Unresolved PR review thread |
| Existing evidence | `research` Issue (`/research` template) |
| New evidence | `experiment` Issue (`/experiment` template) |
| Keep the risk | `/accept-risk` on the PR (Alcove refreshes `decision-review`; reviewer still owns thread resolution) |
| Concrete change | Pull request |

Rules:

- Research and experiment agents **report on Issues**. Fill Conclusion (and Observation for experiments), then move the workflow label to `resolved`.
- Only the **Alcove reviewer** resolves the parent PR thread — when the assumption is handled or the risk is accepted. Opening or closing a research/experiment Issue does not clear the thread.
- `/research` and `/experiment` keep the parent thread **unresolved** until the reviewer re-evaluates.
- Never auto-merge. Never mutate `main` directly.
- Link the parent PR or review thread on research/experiment Issues that answer a review thread. Parent link is optional for planning-first evidence. Link those Issues from the PR when the change depends on them.
- Do **not** open an Issue for every chat question. Issues are for durable evidence; everyday Q&A stays in the agent client.

## Watch (hosted + client-scheduled)

Two valid paths — pick one or both:

1. **Hosted Alcove watch (Pro)** — enable on a linked repo from the dashboard or MCP (`enable_watch`). Alcove runs a Trigger cron, reads optional root `watch.yaml`, and opens/updates a standing Issue titled **Alcove watch** (labels `watch` + `research`). Never mutates `main`.
2. **Client-scheduled** — use your agent client's recurring capability when you live in that client day-to-day.

Optional `watch.yaml` is the **automation config** for this repo: required `schema_version: 1` when the file exists, then generic kinds (`weather` / `infer` / `research`) plus `prompt`, `locations`, and thresholds. Alcove only toggles enablement + cadence. Delete the file or use `checks: []` until you want targets. Do not invent fields — CI validates against `domains/travel/schemas/watch.schema.json`.

Examples of client schedules (pick what your client supports):

- **ChatGPT** — scheduled tasks
- **Claude** — scheduled / recurring tasks or reminders where available
- **Cursor** — cloud agents, Automations, or a recurring `/loop`-style run you set up

Pattern for any of them:

1. Schedule a narrow check — not a full replan.
2. Prefer the client's browser use or built-in connectors when sites block plain fetch.
3. If something **material** changed, open a **pull request** (or a research/experiment Issue if you need evidence first). Never edit `main` from the schedule.
4. Chat agreement is not the record. The PR / Issue is.

Booking stays with the traveler or the client's browser use. Do not treat Alcove or this repo as an auto-booker.

Label vocabulary: see `.github/LABELS.md`. Branch protection: see `docs/branch-protection.md`.
