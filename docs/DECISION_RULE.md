# Decision rule (both cases)

One unified rule classifies **both** cases from the signed difference `D = B − A`,
given the known widths and the gap `g` — `g = 0` for **Case 1** (adjacent),
`g > 0` for **Case 2** (separated).

> **Static reference rule.** The table and function below are the *single-snapshot*
> rule (one reading → one label), verified against ground truth by
> [`tools/unified_static_classifier_test_harness.py`](../tools/unified_static_classifier_test_harness.py)
> (see [`tools/README.md`](../tools/README.md)). The shipped run-time classifier
> [`src/region_classifier/classifier.py`](../src/region_classifier/classifier.py)
> is its **online equivalent**: it never sees `D` directly — it tracks each
> region's boundary via crossing detection + half-width anchors and carries the
> last decided side, which is exactly what `prev_state` stands for here.

**Scope of this rule.** It is stated on the **1-D reduction** of the problem — the
axis crossing both regions, where each region collapses to an interval of width
`W(A)` / `W(B)` separated by `g`. That is the geometry in which "the width" is a
single number, and it is what the harnesses verify. The 2-D scenarios shipped in
[`configs/`](../configs) (circles, rectangles, polygons) are *not* classified by
this table: the run-time classifier works from the distance streams and each
region's `inradius`, and never needs `W(A)`, `W(B)` or `g`. Read this as the proof
of *why* the online design is what it is, not as the code path.

Two preconditions the rule assumes, both far outside any physical setup but worth
naming: the widths must be well clear of the comparison tolerance
(`W(A), W(B) > tol`, else the `D ≥ W(A) + g − tol` branch swallows the region
whole), and likewise `g` is treated as `0` once `g ≤ tol`.

## The rule

```text
┌────────────────────────────────┬──────────────────────────────┬───────────────────────────┐
│ Branch on  D = B − A   (g ≥ 0) │ Result                       │ Case 1 (g = 0) reduces to │
├────────────────────────────────┼──────────────────────────────┼───────────────────────────┤
│ D ≥ W(A) + g                   │ Outside (left of A)          │ D = W(A)                  │
│ g < D < W(A) + g               │ In A                         │ 0 < D < W(A)              │
│ D = g    (g > 0)               │ In A  (A inner-edge plateau) │ folds into D = 0          │
│ −g < D < g    (g > 0)          │ Outside (the gap)            │ folds into D = 0          │
│ D = −g    (g > 0)              │ In B  (B inner-edge plateau) │ —                         │
│ −(W(B)+g) < D < −g             │ In B                         │ −W(B) < D < 0             │
│ D ≤ −(W(B) + g)                │ Outside (right of B)         │ D = −W(B)                 │
│ D = 0    (only when g = 0)     │ In A or In B  (see note)     │ on the shared A/B edge    │
└────────────────────────────────┴──────────────────────────────┴───────────────────────────┘
```

> **Note — the `D = 0` row (shared A/B edge, g = 0 only).** The half-width caps
> decide it where they can (`t > W(B)/2` → In A, `t > W(A)/2` → In B); inside the
> remaining band a lone snapshot is undecidable, so the rule keeps the last
> decided side. The output is therefore **always** In A / In B / Outside —
> **never** a fourth "Ambiguous" label.
>
> **Carrying that side is not sufficient on its own — it must also be *flipped*.**
> When `g = 0`, `D ≡ 0` across the whole right half of A *and* the whole left half
> of B, so the shared-edge crossing produces no change in `D` at all: a reader who
> implements "keep the last decided side" and nothing else keeps answering `In A`
> straight through half of region B. Measured on a left-to-right traversal, that is
> a **20% error rate** for `W(A) = W(B) = 4` (the entire left half of B), and 12.5%
> for `W(A) = 7, W(B) = 3`. The missing ingredient is the crossing detector: at a
> shared-edge crossing *both* distances dip to ~0 together, which is the event that
> flips the carried bit. `classifier.py` does exactly this, which is why it scores
> ~99.7% on [`configs/adjacent_bands.yaml`](../configs/adjacent_bands.yaml) while
> the bare table would not. Take the `D = 0` row as "the snapshot cannot decide —
> defer to state", not as a complete online algorithm.

## The function

```python
def classify(A, B, W_A, W_B, g, prev_state='Outside', tol=1e-9):
    """Static single-snapshot rule on D = B - A (both cases).
    g = 0 -> Case 1 (adjacent);  g > 0 -> Case 2 (separated).
    prev_state (the last decided label) is used ONLY for the Case-1 g=0 band,
    where a lone snapshot is undecidable; for g > 0 it is never consulted.
    It defaults to 'Outside' -- never None -- so that a cold start inside the
    band still returns a real label, matching classifier.py, which begins with
    both membership bits False. That first label is a guess; a clean crossing or
    an outer-edge entry re-anchors it.
    """
    D = B - A
    if D >= W_A + g - tol:     return 'Outside'   # left of A
    if D <= -(W_B + g) + tol:  return 'Outside'   # right of B
    if D >  g + tol:           return 'In A'      # A side
    if D < -g - tol:           return 'In B'      # B side
    if g > tol:                                   # Case 2: the gap is Outside
        if D >=  g - tol:      return 'In A'      # inner-edge plateau (+g)
        if D <= -g + tol:      return 'In B'      # inner-edge plateau (-g)
        return 'Outside'                          # inside the gap
    # Case 1 (g == 0): D ~ 0 is the shared A/B edge
    t = A
    if t > W_B / 2 + tol:      return 'In A'
    if t > W_A / 2 + tol:      return 'In B'
    return prev_state          # band: keep the last decided side (never "Ambiguous")
```

Step-by-step figures for each branch are in [`figures/`](figures/) (indexed in
its `README.md`).
