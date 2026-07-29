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
| D | Carrying the last decided side is **not sufficient alone**; the crossing detector is the missing half |

Latest run: 560,000 samples per case, 0 confident-wrong and 0 wrongly-abstained in
both.

**On Test D — and a trap worth knowing about.** An earlier version of this test fed
the *ground-truth* label in as `prev_state` and then asserted the output equalled
it. Since `resolve_band_with_state` returns `prev_state` whenever the snapshot is
ambiguous, that version returned the truth by construction: it could not fail, and
so proved nothing. It now walks a trajectory carrying only its own **previous
output**, which makes it falsifiable — and it duly fails:

```
wA=4.0  wB=4.0  carry-only     :   8000/40000 wrong ( 20.0%)
wA=4.0  wB=4.0  carry+crossing :      1/40000 wrong (  0.0%)
wA=7.0  wB=3.0  carry-only     :   5000/40001 wrong ( 12.5%)
wA=7.0  wB=3.0  carry+crossing :      1/40001 wrong (  0.0%)
wA=2.0  wB=8.0  carry-only     :   3333/40000 wrong (  8.3%)
wA=2.0  wB=8.0  carry+crossing :      1/40000 wrong (  0.0%)
```

The reason is worth stating plainly: when `g = 0`, `D ≡ 0` across the whole right
half of A *and* the whole left half of B, so crossing the shared edge changes
nothing in `D`. A classifier that only *keeps* the last side therefore answers
`In A` straight through half of region B — hence the 20% (which is exactly the
fraction of the world that B's left half occupies). What supplies the flip is the
crossing detector: at a shared-edge crossing *both* distances dip to ~0 and
rebound together. Test D's `Dip` class mirrors the adaptive-threshold, dip-and-
rebound mechanism in
[`classifier.py`](../src/region_classifier/classifier.py), and with it the error
drops to a single transient sample per crossing — the causal one-tick lag that
[`../README.md`](../README.md) documents.

## `static_classifier_test_harness.py`

The earlier Case-1-only (adjacent, shared border) harness that established *why*
state is needed at all. Test 3 is the impossibility proof: for `wA = wB = 4`, the
positions `x = 3` (In A) and `x = 5` (In B) both report `(A, B) = (1.0, 1.0)` — so
no static rule over `(A, B, wA, wB)` can separate them, and the ambiguity is a
property of the *inputs*, not of any particular classifier. Test 4 then shows one
bit of carried state removes the whole band.

Latest run: 480,000 samples, 0 confident-wrong, 0 wrongly-abstained, 0 errors in
Test 4.

## `sweep_2d.py`

The other two harnesses verify the 1-D reference *rule*. This one exercises the
**shipped 2-D pipeline** — `RegionField` (circle / rectangle / polygon) → `Sensor`
→ `RegionClassifier` — over 18 geometry pairings in both configurations, with
randomised sizes, motion, `dt` and distance noise:

```bash
python tools/sweep_2d.py --quick      # smoke run
python tools/sweep_2d.py              # 2.7M ticks per cold-start mode
```

Latest full run — 540 scenarios × 5,000 ticks per mode:

| Cold start | Accuracy | Worst pairing | Ticks to lock on |
|:--|:--|:--|:--|
| **Outside** (matches the simulator) | **96.8%** | 94.7% | median 49, p90 49 |
| **Inside A** (adversarial) | 92.7% | 86.4% | median 173, p90 435 |

Two things the script is deliberately careful about, because both were found to
matter more than expected:

* **Sampling regime.** The control variable is `speed·dt / inradius`. The shipped
  configs sit near `0.03`. Pushed to `~0.2`, the *ground truth itself* flips every
  couple of ticks, and a causal detector — which needs a dip *and* a rebound, so
  ≥3 samples — cannot track that at any accuracy; measured accuracy collapses to
  ~60%. That is a Nyquist limit, not a classifier defect, which is why the sweep
  stays in `[0.005, 0.05]` unless you pass `--ratio-max`.
* **Cold start is reported separately, not blended.** Started inside a region, the
  first boundary exit inverts that region's membership bit and only the half-width
  anchor can reset it, which needs the sensor to travel more than one `inradius`
  clear of the region. Hence the median 173 ticks. See the note in
  [`../README.md`](../README.md).

## Relation to the shipped classifier

`resolve_band_with_state(..., prev_state)` here is the harness's explicit form of
what [`classifier.py`](../src/region_classifier/classifier.py) carries implicitly
in `_RegionState.inside` — kept across ticks and flipped by crossing detection
rather than passed in. These scripts are not part of the `pytest` suite (they take
~10 s and assert by printing counts); the packaged behaviour is covered by
[`tests/`](../tests).
