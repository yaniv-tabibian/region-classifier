# Verification harnesses

Standalone scripts that verify the **static reference rule** documented in
[`../docs/DECISION_RULE.md`](../docs/DECISION_RULE.md) — the single-snapshot form
(one reading → one label) of which the shipped
[`classifier.py`](../src/region_classifier/classifier.py) is the online equivalent.

They are deliberately self-contained: no imports from `region_classifier`, a 1-D
reduction of the geometry, and their own ground truth. That independence is the
point — they check the *rule*, not the implementation, so a bug in one cannot hide
a bug in the other. Run either directly, no install needed:

```bash
python tools/unified_static_classifier_test_harness.py
python tools/static_classifier_test_harness.py
```

## `unified_static_classifier_test_harness.py`

Verifies the **one unified rule over both cases** (`g = 0` adjacent, `g > 0`
separated) against ground truth, over random widths on a dense position grid:

| Test | Asserts |
|:--|:--|
| A | Case 2 (`g > 0`): 0 wrong, and **0 abstentions** — a single snapshot is exact |
| B | Case 1 (`g = 0`): 0 wrong; abstains *only* inside the provably undecidable band |
| C | The gap is what removes the Case-1 ambiguity — same construction, distinct `D` |
| D | **One bit** of carried state (`resolve_band_with_state`) clears the band: 0 errors |

Latest run: 560,000 samples per case, 0 confident-wrong and 0 wrongly-abstained in
both; 0 errors in Test D.

## `static_classifier_test_harness.py`

The earlier Case-1-only (adjacent, shared border) harness that established *why*
state is needed at all. Test 3 is the impossibility proof: for `wA = wB = 4`, the
positions `x = 3` (In A) and `x = 5` (In B) both report `(A, B) = (1.0, 1.0)` — so
no static rule over `(A, B, wA, wB)` can separate them, and the ambiguity is a
property of the *inputs*, not of any particular classifier. Test 4 then shows one
bit of carried state removes the whole band.

Latest run: 480,000 samples, 0 confident-wrong, 0 wrongly-abstained, 0 errors in
Test 4.

## Relation to the shipped classifier

`resolve_band_with_state(..., prev_state)` here is the harness's explicit form of
what [`classifier.py`](../src/region_classifier/classifier.py) carries implicitly
in `_RegionState.inside` — kept across ticks and flipped by crossing detection
rather than passed in. These scripts are not part of the `pytest` suite (they take
~10 s and assert by printing counts); the packaged behaviour is covered by
[`tests/`](../tests).
