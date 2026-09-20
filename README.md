# Japan summer 2026

A starter itinerary for a 10-night Japan trip: Tokyo → Hakone → Kyoto → Tokyo. Opinionated hard checks ship with the sample. Not the full private record, and not postmortems or traveler profiles.

Fork it. Edit the plan. Delete `STARTER.md`, set `starter: false`, replace `traveler_ids`. Checks fail until you do.

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 -m engine.facts
python3 -m engine.check
```

`engine.facts` always prints. `engine.check` fails on this starter on purpose.

Cursor, Claude, and ChatGPT should follow `AGENTS.md`.

## Alcove review

Install the Alcove GitHub App on the fork for adversarial PR review. Soft findings stay as unresolved conversation threads; the App's `decision-review` status check runs alongside the deterministic `check` workflow. Protect `main` as described in [`docs/branch-protection.md`](docs/branch-protection.md). Evidence for open concerns goes in Research / Experiment Issues (see `.github/ISSUE_TEMPLATE/` and `.github/LABELS.md`) — never auto-merge, never edit `main` directly.
