# Labels

Small label set for this trip repo. Create these in GitHub Settings → Labels (or via `gh label create`) if they are missing after a fork.

## Type

| Label | Meaning |
| --- | --- |
| `research` | Retrieving existing evidence (sources, docs, prior facts). |
| `experiment` | Generating new evidence via a dry-run. Does not mutate `main`. |
| `risk` | Optional later — accepted or tracked residual risk; not required for MVP. |

An Issue is either research or experiment, not both.

## Workflow

| Label | Meaning |
| --- | --- |
| `proposed` | Opened; work not started (or waiting on intake). |
| `in-progress` | Someone is actively researching or running the experiment. |
| `resolved` | Conclusion filled; ready for the Alcove reviewer to re-evaluate the parent PR thread. |

Keep exactly one workflow label current. Issue templates start Issues with `proposed`.

## Not labels

- PR review threads stay unresolved until the **Alcove reviewer** decides the assumption is handled or the risk is accepted.
- Deterministic CI failures are status checks, not labels.
