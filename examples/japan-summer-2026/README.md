# Example: Japan summer 2026

A complete 10-night sample plan (Tokyo → Hakone → Kyoto → Tokyo), adapted as a public illustration. Not a private record; no traveler profiles or postmortems.

This folder is **not** your live trip. Your accepted plan is the repo root (`main`).

## Try the checks against this example

From the repository root:

```bash
python3 -m engine.facts --root examples/japan-summer-2026 --domain-root domains
python3 -m engine.check --root examples/japan-summer-2026 --domain-root domains
```

This folder is sample plan data only — copy into the repo root to use it.

## Use it in your fork

1. Copy `trip.yaml`, `budget.yaml`, and the `itinerary/`, `bookings/`, `dependencies/` trees into the repo root (overwrite the empty scaffold).
2. Edit for your dates and party.
3. Open PRs for changes — never treat chat agreement as the record.
