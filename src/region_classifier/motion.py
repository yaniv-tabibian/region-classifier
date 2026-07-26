"""Realistic 2D motion generator.

A correlated random walk with waypoint steering: the sensor wanders between a
cycle of targets (region A, an outside point, region B, another outside point)
so the path naturally visits all three states. Heading changes slowly
(correlated), and speed follows an Ornstein-Uhlenbeck process around a mean, so
the average speed is fixed but the instantaneous speed is NOT constant -- the
"realistic real-world behavior" the assignment asks for.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import atan2, cos, pi, sin

import numpy as np

Point = tuple[float, float]


@dataclass
class MotionParams:
    mean_speed: float = 1.2
    speed_sigma: float = 0.6  # OU volatility of speed
    speed_revert: float = 1.5  # OU mean-reversion rate
    turn_sigma: float = 0.5  # heading diffusion (rad/sqrt(s))
    steer_gain: float = 1.2  # how strongly heading is pulled to the target
    waypoint_radius: float = 2.0  # switch target when this close


class CorrelatedRandomWalk:
    def __init__(
        self,
        rng: np.random.Generator,
        bounds: tuple[float, float, float, float],
        waypoints: Sequence[Point],
        params: MotionParams,
        start: Point | None = None,
    ) -> None:
        if not waypoints:
            raise ValueError("need at least one waypoint")
        self._rng = rng
        self._xmin, self._ymin, self._xmax, self._ymax = bounds
        self._wp = [np.asarray(w, dtype=float) for w in waypoints]
        self._p = params
        self._wp_idx = 0
        if start is None:
            start = (self._xmin + 1.0, self._ymin + 1.0)  # a corner -> Outside
        self._pos = np.asarray(start, dtype=float)
        self._speed = params.mean_speed
        self._heading = float(rng.uniform(0.0, 2.0 * pi))

    @property
    def pos(self) -> np.ndarray:
        return self._pos.copy()

    @staticmethod
    def _wrap(angle: float) -> float:
        return (angle + pi) % (2.0 * pi) - pi

    def step(self, dt: float) -> np.ndarray:
        target = self._wp[self._wp_idx]
        rng, p = self._rng, self._p

        # steer heading toward the target, plus correlated noise
        desired = atan2(target[1] - self._pos[1], target[0] - self._pos[0])
        self._heading += (
            self._wrap(desired - self._heading) * p.steer_gain * dt
            + p.turn_sigma * (dt**0.5) * rng.standard_normal()
        )
        self._heading = self._wrap(self._heading)

        # Ornstein-Uhlenbeck speed: fixed mean, fluctuating instantaneous value
        self._speed += (
            p.speed_revert * (p.mean_speed - self._speed) * dt
            + p.speed_sigma * (dt**0.5) * rng.standard_normal()
        )
        self._speed = max(0.05 * p.mean_speed, self._speed)

        self._pos = self._pos + self._speed * dt * np.array(
            [cos(self._heading), sin(self._heading)]
        )

        # reflect at the pasture bounds
        if self._pos[0] < self._xmin or self._pos[0] > self._xmax:
            self._pos[0] = float(np.clip(self._pos[0], self._xmin, self._xmax))
            self._heading = self._wrap(pi - self._heading)
        if self._pos[1] < self._ymin or self._pos[1] > self._ymax:
            self._pos[1] = float(np.clip(self._pos[1], self._ymin, self._ymax))
            self._heading = self._wrap(-self._heading)

        if float(np.hypot(*(self._pos - target))) < p.waypoint_radius:
            self._wp_idx = (self._wp_idx + 1) % len(self._wp)

        return self._pos.copy()
