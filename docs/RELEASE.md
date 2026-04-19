# Release Process

## Versioning
- Follow semantic versioning with `vX.Y.Z` tags.
- Update `pyproject.toml` version and `CHANGELOG.md` in the same PR.

## Pre-Release Checklist
- CI is green on the release branch.
- `python -m ruff check .` passes.
- `python -m unittest discover -s tests` passes.
- `python -m build` succeeds.
- Security and PHI controls reviewed for changed surfaces.

## Release Steps
1. Merge release PR to `main`.
2. Create and push a tag: `vX.Y.Z`.
3. Validate `Release Validation` workflow success.
4. Publish artifacts from `dist/` to the package registry.

## Rollback Guidance
- If release checks fail post-tag, issue a patch release.
- If production behavior regresses, roll back to previous tag and redeploy.
