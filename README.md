# Alcove trip starter — Japan

Empty Japan trip scaffold for GitHub-first planning. Fork it, fill it in, plan via ChatGPT / Claude / Cursor. CI on `main` stays green for the empty scaffold.

**Português (Brasil):** [`docs/pt-BR/README.md`](docs/pt-BR/README.md) · [`docs/pt-BR/AGENTS.md`](docs/pt-BR/AGENTS.md). Machine contracts (YAML keys, Issue headings, `/research`) stay English.

A fleshed **example** itinerary lives under [`examples/japan-summer-2026/`](examples/japan-summer-2026/) — open that folder (or run checks against it) to see a complete sample. Copy what you want into the repo root; do not treat the example as your accepted trip.

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 -m engine.facts
python3 -m engine.check
```

`engine.facts` always prints. `engine.check` should pass on this empty scaffold. It fails when the plan is internally impossible (schema, times, configured hard limits, secret/PII shapes).

To inspect the example:

```bash
python3 -m engine.facts --root examples/japan-summer-2026 --domain-root domains
python3 -m engine.check --root examples/japan-summer-2026 --domain-root domains
```

## Make it yours

1. Replace `traveler_ids`, dates, and title in `trip.yaml`.
2. Add nodes under `itinerary/`, `bookings/`, `dependencies/` (or copy from the example).
3. Retune `hard_constraints` if the Japan defaults do not fit.
4. Open PRs for changes — chat is not the record.

Cursor, Claude, and ChatGPT should follow `AGENTS.md`.

## Alcove review

Install the Alcove GitHub App on the fork for adversarial PR review. Soft findings stay as unresolved conversation threads; the App's `decision-review` status check runs alongside the deterministic `check` workflow. Protect `main` as described in [`docs/branch-protection.md`](docs/branch-protection.md). Evidence for open concerns goes in Research / Experiment Issues (see `.github/ISSUE_TEMPLATE/` and `.github/LABELS.md`) — never auto-merge, never edit `main` directly.

## Watch (hosted + client-scheduled)

Want Fuji visibility, weather, or deadlines re-checked over time?

- **Hosted (Pro)** — enable watch on the linked repo in Alcove (dashboard or MCP). Optional root [`watch.yaml`](watch.yaml) lists narrow checks (`schema_version: 1` required when the file exists); Alcove updates a standing **Alcove watch** Issue (never edits `main`). CI validates the file via `domains/travel/schemas/watch.schema.json`.
- **Client-scheduled** — a recurring task in ChatGPT / Claude / Cursor (or similar) remains fully valid.

If something material changes, open a PR (or a research/experiment Issue). Booking stays in the client or with you. Details: [`AGENTS.md`](AGENTS.md).
