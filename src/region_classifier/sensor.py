"""The sensor: hides the true position and exposes ONLY the two distance getters.

This mirrors the assignment: the classifier must work from ``get_dist_a()`` and
``get_dist_b()`` (which take no arguments) and never sees the position.
``true_label()`` and ``position()`` exist only for the simulator's validation
and visualisation and must not be used by the classifier.
"""

from __future__ import annotations

import numpy as np

from .geometry import RegionField
from .motion import CorrelatedRandomWalk


class Sensor:
    def __init__(
        self,
        field: RegionField,
        motion: CorrelatedRandomWalk,
        rng: np.random.Generator,
        distance_noise_std: float = 0.0,
    ) -> None:
        self._field = field
        self._motion = motion
        self._rng = rng
        self._noise = distance_noise_std
        self._pos = motion.pos
        self._d_a = self._field.dist_a(*self._pos)
        self._d_b = self._field.dist_b(*self._pos)

    def step(self, dt: float) -> None:
        self._pos = self._motion.step(dt)
        na = self._rng.normal(0.0, self._noise) if self._noise > 0 else 0.0
        nb = self._rng.normal(0.0, self._noise) if self._noise > 0 else 0.0
        self._d_a = max(0.0, self._field.dist_a(*self._pos) + na)
        self._d_b = max(0.0, self._field.dist_b(*self._pos) + nb)

    # --- the only interface the classifier may use ---
    def get_dist_a(self) -> float:
        return self._d_a

    def get_dist_b(self) -> float:
        return self._d_b

    # --- validation / visualisation only ---
    def true_label(self) -> str:
        return self._field.true_label(*self._pos)

    def position(self) -> tuple[float, float]:
        return (float(self._pos[0]), float(self._pos[1]))
