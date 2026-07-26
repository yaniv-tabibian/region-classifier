"""Online region classifier.

The classifier receives, once per tick, only the two unsigned
shortest-distance-to-boundary values (``d_a``, ``d_b``). A single sample is
ambiguous (being 3 m inside a region and 3 m outside it both read 3), so the
decision is recovered over time from two mechanisms:

1. **Half-width anchors** — an interior point of a region is at most
   ``inradius`` from its boundary, so ``d > inradius`` proves we are *outside*
   that region. This is certain, needs no history, and makes the classifier
   self-correcting (it can never get permanently stuck in a wrong state).

2. **Boundary-crossing detection** — a boundary crossing is the moment a
   distance dips to ~0 and rebounds. Each crossing toggles that region's
   membership. The near-zero threshold is adaptive: near a transversal crossing
   ``|Δd|`` ≈ speed·dt, so the smallest sampled distance is ~speed·dt; the
   threshold tracks the recent ``|Δd|`` and therefore self-scales with the
   (non-constant) speed.

The algorithm is causal and O(1) in time and memory per sample.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import inf


@dataclass
class _RegionState:
    inside: bool = False
    prev: float | None = None
    falling: bool = False
    local_min: float = inf
    eps: float = 0.0  # running estimate of |Δd| (~ speed·dt)
    ema: float | None = None  # smoothed distance (if smoothing enabled)


class RegionClassifier:
    def __init__(
        self,
        inradius_a: float,
        inradius_b: float,
        crossing_k: float = 1.4,
        eps_decay: float = 0.85,
        eps_floor: float = 1e-6,
        anchor_margin: float = 0.0,
        smoothing: float = 0.0,
    ) -> None:
        self._r = {"a": inradius_a, "b": inradius_b}
        self._crossing_k = crossing_k
        self._eps_decay = eps_decay
        self._eps_floor = eps_floor
        self._anchor_margin = anchor_margin
        self._smoothing = smoothing
        self._st = {"a": _RegionState(), "b": _RegionState()}

    # -- per-region update -------------------------------------------------
    def _update_region(self, key: str, d_raw: float) -> None:
        st = self._st[key]
        inradius = self._r[key]

        if self._smoothing > 0.0:
            st.ema = (
                d_raw
                if st.ema is None
                else (self._smoothing * st.ema + (1.0 - self._smoothing) * d_raw)
            )
            d = st.ema
        else:
            d = d_raw

        if st.prev is not None:
            delta = d - st.prev
            st.eps = max(self._eps_decay * st.eps, abs(delta))
            thr = max(self._crossing_k * st.eps, self._eps_floor)
            if delta < 0.0:  # descending toward a boundary
                st.falling = True
                st.local_min = min(st.local_min, d)
            elif delta > 0.0:  # ascending: a local minimum passed
                if st.falling and st.local_min <= thr:
                    st.inside = not st.inside  # crossed the boundary
                st.falling = False
                st.local_min = d
        else:
            st.local_min = d

        if d > inradius + self._anchor_margin:  # certain: outside this region
            st.inside = False
        st.prev = d

    # -- public API --------------------------------------------------------
    def update(self, d_a: float, d_b: float) -> str:
        """Feed one sample of both distances; return the current label."""
        self._update_region("a", d_a)
        self._update_region("b", d_b)

        sa, sb = self._st["a"], self._st["b"]
        if sa.inside and sb.inside:
            # regions are disjoint: cannot be inside both. Keep the one we are
            # deeper inside (larger distance to its own boundary).
            if d_a >= d_b:
                sb.inside = False
            else:
                sa.inside = False
        return self.label

    @property
    def label(self) -> str:
        if self._st["a"].inside:
            return "In A"
        if self._st["b"].inside:
            return "In B"
        return "Outside"
