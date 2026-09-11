# Agent instructions

This repo turns Google Maps saved-place lists into categorized data for
import into a map tool. See `README.md` for pipeline usage.

## Decisions must be recorded

When making or changing an architectural/process decision for this project
(geocoding approach, categorization approach, data/output structure, which
external tools or APIs to depend on, etc.) - not routine implementation
details - record it in `decisions/` following the template in
`decisions/README.md`. Check `decisions/` before revisiting a past choice,
and update the relevant file's Status (e.g. to "Superseded by NNNN") rather
than leaving stale docs.

## Working conventions

- Never commit directly to `main`. Work on a `claude/*` branch, push, open
  a PR.
- Free to merge your own PRs without waiting for human review. Keep CI
  light or nonexistent (this project intentionally avoids spending GitHub
  Actions minutes) and don't bloat the repo with generated cruft.
- "Automatically delete head branches" is on in repo settings - merged
  branches clean themselves up.
- Be economical with tokens; this is a small personal project, not one
  that warrants heavy automated pipelines for its current data volume.
