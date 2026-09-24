# Alcove trip starter

A fresh trip with the structure and checks already in place. Plan in ChatGPT, Claude, Cursor, or another agent client; review proposed changes in GitHub and merge the ones you accept.

There are no sample itineraries, bookings, traveler profiles, or watch targets to clean up. Unknown values stay `null`, and personal hard limits start unset. Passing CI means the current records satisfy the checks; it does not mean an unfinished trip is ready to take.

## Start planning

1. Create your own repository from these files. Choose a **private repository** for personal planning; forking a public repository does not make it private.
2. Ask your agent to start planning with you and follow [`AGENTS.md`](AGENTS.md). It can fill in your trip name, dates, travelers, budget, and constraints as you decide them. You do not need to choose everything at setup.
3. Review and merge small proposals as you go. `main` is the accepted trip; chat alone does not change it.

Keep the configuration, schemas, engine, and GitHub workflow. They provide the checks for every new trip. The empty record folders are ready for your plans:

| Path | Purpose |
| --- | --- |
| `trip.yaml` | Trip identity, dates, opaque traveler IDs, route, and accepted hard limits |
| `budget.yaml` | Budget currency, estimates, and an optional hard cap |
| `itinerary/`, `bookings/`, `dependencies/` | Plans, commitments, and prerequisites |
| `evidence/`, `actuals/` | Supporting evidence and explicitly recorded outcomes |
| `watch.yaml` | Optional checks of changing external conditions; starts empty |
| `repo.yaml`, `domains/travel/` | Domain selection, record schemas, rules, and review facts |
| `engine/`, `tests/`, `.github/` | Validation, isolated test fixtures, and GitHub checks |

Traveler profiles and cross-trip lessons stay in Alcove; only opaque traveler IDs belong here. Your agent should use the schemas for record shapes and leave unknowns unset.

## Run the checks

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 -m engine.facts --check
python3 -m engine.check
```

`engine.facts` produces review context. `engine.check` enforces schema, chronology, required references, configured hard limits, and secret/PII patterns. Unset limits do not impose personal preferences. A budget hard cap requires a currency.

Tests build small synthetic records in temporary directories. Those records are never loaded as part of your trip.

## Alcove review

Install the Alcove GitHub App with access to your repository, then enable review for it in Alcove. Soft findings stay as unresolved conversation threads; the App's `decision-review` status check runs alongside the deterministic `check` workflow. Protect `main` as described in [`docs/branch-protection.md`](docs/branch-protection.md). Evidence for open concerns goes in Research / Experiment Issues (see `.github/ISSUE_TEMPLATE/` and `.github/LABELS.md`) — never auto-merge, never edit `main` directly.

## Watch (hosted + client-scheduled)

Add watch targets once you know what needs checking:

- **Hosted (Pro)** — enable watch on the linked repo in Alcove (dashboard or MCP). Optional root [`watch.yaml`](watch.yaml) lists narrow checks (`schema_version: 1` required when the file exists); Alcove updates a standing **Alcove watch** Issue (never edits `main`). CI validates the file via `domains/travel/schemas/watch.schema.json`.
- **Client-scheduled** — a recurring task in ChatGPT / Claude / Cursor (or similar) remains fully valid.

If something material changes, open a PR (or a research/experiment Issue). Booking stays in the client or with you. Details: [`AGENTS.md`](AGENTS.md).
