# Optional deep / stress tests

These are extra, self-contained robustness tests (property + stress). They are
**not required** for the project to work and can be removed at any time.

## How to delete them (one step, no side effects)

```bash
rm -rf tests/stress        # or delete this folder in your file manager
```

Nothing else depends on this folder:
- No changes to `pyproject.toml` or `.github/workflows/ci.yml` are needed to add
  or remove it — the normal `pytest` run (and therefore CI) simply collects one
  fewer folder.
- The core suite in `tests/` is unaffected.

## What they check
- `test_anchor_invariant.py` — the classifier's half-width **anchor guarantee**:
  it never reports `In A` while `d_a > inradius_a + margin` (same for B), and
  never both at once — i.e. no valid distance value falls into a wrong branch.
- `test_random_scenarios.py` — end-to-end accuracy on many **random** Case-1
  (adjacent) and Case-2 (separated) 2-D scenarios stays high.
