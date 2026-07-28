# Figures

Explanatory diagrams for the design write-up and [`../DECISION_RULE.md`](../DECISION_RULE.md).
They illustrate the 1-D reasoning behind the classifier (`D = B − A`, the two
geometries, and the decision at each branch). Runtime output (the live demo GIF)
lives separately under [`../../examples/`](../../examples).

## Overview

- **`14.0 - Both cases - unified D-axis summary.png`** — the whole decision on
  `D = B − A` for both cases, on one axis. Start here.
- **`Case1 - region layout and D decision.png`** — Case 1 at a glance: region
  layout (top) → decision on `D` (bottom).
- **`interviewer_sketch_interpretation.png`** — interpretation of the
  interviewer's whiteboard sketch (the numbered points and the two distance lines).

## Case 1 (adjacent, gap = 0) — step-by-step

- **`01 - Case1 setup.png`** — setup: regions A and B sharing an edge; the two
  distances and the widths `W(A)`, `W(B)`.
- **`02 - Case1 step1 D=0 band.png`** — when `D = 0` (`A = B`): the shared-edge straddle.
- **`03 - Case1 step2 half-width cap.png`** — the half-width cap (an interior
  point is at most `W/2` from a boundary).
- **`04 - Case1 step3 tie-break.png`** — the width test that decides In A vs In B,
  and the residual undecidable band.
- **`05 - Case1 InB (-W(B) less D less 0).png`** — condition `−W(B) < D < 0` ⇒ In B.
- **`06 - Case1 Outside right (D = -W(B)).png`** — condition `D = −W(B)` ⇒ Outside (right of B).

## Both cases — the unified rule per branch

- **`14.1 - Unified D ge W(A)+g - Outside left of A.png`** — `D ≥ W(A)+g` ⇒ Outside (left of A).
- **`14.2 - Unified g less D less W(A)+g - In A.png`** — `g < D < W(A)+g` ⇒ In A.
- **`14.3 - Unified D = g - In A inner-edge plateau.png`** — `D = g` ⇒ In A (inner-edge plateau).
- **`14.4 - Unified -g less D less g - Outside the gap.png`** — `−g < D < g` ⇒ Outside (the gap).
- **`14.5 - Unified D = -g - In B inner-edge plateau.png`** — `D = −g` ⇒ In B (inner-edge plateau).
- **`14.6 - Unified -(W(B)+g) less D less -g - In B.png`** — `−(W(B)+g) < D < −g` ⇒ In B.
- **`14.7 - Unified D le -(W(B)+g) - Outside right of B.png`** — `D ≤ −(W(B)+g)` ⇒ Outside (right of B).
- **`14.8 - D=0 on shared edge (g=0).png`** — `D = 0` (Case 1 only): on the shared
  edge, the widths decide the side.
- **`14.9 - Unified classifier code map.png`** — the `classify()` code mapped onto
  the `D`-axis branches.

## Why single snapshots aren't always enough

- **`ambiguity_resolution.png`** — a lone snapshot can be provably undecidable
  (mirror twins across the shared edge) ↔ the stream resolves it at run time.
- **`case2_decidable.png`** — Case 2 has no undecidable band: the gap removes the
  twins; the `D`-axis decision map for the separated case.
