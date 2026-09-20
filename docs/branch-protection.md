# Branch protection (forks)

`main` is the accepted trip. Forks should protect it so agents propose and humans merge.

## Recommended settings

In **Settings → Branches → Branch protection rule** for `main`:

1. **Require a pull request before merging**
2. **Require conversation resolution before merging** — material Alcove review findings stay as unresolved threads until handled or risk-accepted
3. **Require status checks to pass before merging**, including at least:
   - Deterministic engine CI — the existing GitHub Actions workflow named `check` (job `check`)
   - `decision-review` — the Alcove GitHub App check (appears after the App is installed on the fork)
4. **Do not enable GitHub auto-merge** for this product — a human traveler merges after review

Optional but useful: require branches to be up to date before merging; restrict who can push to `main`.

## Why

- Hard invariants belong in `engine.check` / the `check` workflow.
- Soft / adversarial concerns belong in Alcove PR review comments and threads.
- Research and experiment Issues gather evidence; they do **not** resolve the parent review thread. Only the Alcove reviewer does that after re-evaluation.

See `AGENTS.md` for the evidence loop agents follow.
