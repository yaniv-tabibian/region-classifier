# Decision rule (both cases)

One unified rule classifies **both** cases from the signed difference `D = B − A`,
given the known widths and the gap `g` — `g = 0` for **Case 1** (adjacent),
`g > 0` for **Case 2** (separated).

> **Static reference rule.** The table and function below are the *single-snapshot*
> rule (one reading → one label), used by `unified_static_classifier_test_harness.py`
> to verify the geometry. The shipped run-time classifier
> [`src/region_classifier/classifier.py`](../src/region_classifier/classifier.py)
> is its **online equivalent**: it never sees `D` directly — it tracks each
> region's boundary via crossing detection + half-width anchors and carries the
> last decided side, which is exactly what `prev_state` stands for here.

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

## The function

```python
def classify(A, B, W_A, W_B, g, prev_state=None, tol=1e-9):
    """Static single-snapshot rule on D = B - A (both cases).
    g = 0 -> Case 1 (adjacent);  g > 0 -> Case 2 (separated).
    prev_state (the last decided label) is used ONLY for the Case-1 g=0 band,
    where a lone snapshot is undecidable; for g > 0 it is never consulted.
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
