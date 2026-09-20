# Alcove trip starter — Japan

Empty Japan trip scaffold for GitHub-first planning. Fork it, claim it, plan via ChatGPT / Claude / Cursor. A fleshed **example** itinerary lives under [`examples/japan-summer-2026/`](examples/japan-summer-2026/) — open that folder (or run checks against it) to see a complete sample; do not treat it as your `main`.

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 -m engine.facts
python3 -m engine.check
```

`engine.facts` always prints. `engine.check` fails on this unclaimed scaffold on purpose (delete `STARTER.md`, set `starter: false`, replace placeholders).

To inspect the example:

```bash
python3 -m engine.facts --root examples/japan-summer-2026 --domain-root domains
python3 -m engine.check --root examples/japan-summer-2026 --domain-root domains
```

Cursor, Claude, and ChatGPT should follow `AGENTS.md`.

## Alcove review

Install the Alcove GitHub App on the fork for adversarial PR review. Soft findings stay as unresolved conversation threads; the App's `decision-review` status check runs alongside the deterministic `check` workflow. Protect `main` as described in [`docs/branch-protection.md`](docs/branch-protection.md). Evidence for open concerns goes in Research / Experiment Issues (see `.github/ISSUE_TEMPLATE/` and `.github/LABELS.md`) — never auto-merge, never edit `main` directly.

## Reality watch (no Alcove cron)

Want fares, hours, or deadlines re-checked over time? Use a **scheduled / recurring task in your agent client** (ChatGPT, Claude, Cursor, or similar) — not an Alcove background job. If something material changes, have the agent open a PR (or a research/experiment Issue). Never edit `main` from the schedule. Booking stays in the client (browser use / connectors) or with you; this repo only records the accepted plan. Details live in [`AGENTS.md`](AGENTS.md).
