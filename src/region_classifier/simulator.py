"""Ties the pieces together and runs the real-time loop.

Each tick: advance the sensor, read the two getters, classify, emit. Nothing is
buffered for the decision -- the label is produced online (no post-processing).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from .classifier import RegionClassifier
from .config import SimConfig
from .geometry import RegionField
from .motion import CorrelatedRandomWalk
from .sensor import Sensor

LABELS = ("In A", "In B", "Outside")


@dataclass
class Tick:
    t: float
    d_a: float
    d_b: float
    label: str
    truth: str | None = None
    x: float = 0.0
    y: float = 0.0


@dataclass
class RunStats:
    ticks: int = 0
    matched: int = 0

    @property
    def accuracy(self) -> float:
        return self.matched / self.ticks if self.ticks else 0.0


def build(config: SimConfig):
    rng = np.random.default_rng(config.seed)
    field = RegionField(config.region_a, config.region_b)
    motion = CorrelatedRandomWalk(rng, config.pasture, config.waypoints, config.motion)
    sensor = Sensor(field, motion, rng, config.distance_noise_std)
    anchor_margin = 3.0 * config.distance_noise_std
    clf = RegionClassifier(
        inradius_a=config.region_a.inradius,
        inradius_b=config.region_b.inradius,
        anchor_margin=anchor_margin,
        smoothing=config.smoothing,
    )
    return field, sensor, clf


def run(
    config: SimConfig,
    reporter: Callable[[Tick], None] | None = None,
    realtime: bool = True,
    validate: bool = False,
    max_steps: int | None = None,
) -> RunStats:
    _field, sensor, clf = build(config)
    stats = RunStats()
    n_steps = int(round(config.duration_s / config.dt))
    if max_steps is not None:
        n_steps = min(n_steps, max_steps)

    for i in range(n_steps):
        start = time.perf_counter()
        sensor.step(config.dt)
        d_a = sensor.get_dist_a()
        d_b = sensor.get_dist_b()
        label = clf.update(d_a, d_b)

        truth = sensor.true_label() if (validate or reporter) else None
        if validate:
            stats.ticks += 1
            stats.matched += int(label == truth)

        if reporter is not None:
            x, y = sensor.position()
            reporter(
                Tick(
                    t=i * config.dt,
                    d_a=d_a,
                    d_b=d_b,
                    label=label,
                    truth=truth,
                    x=x,
                    y=y,
                )
            )

        if realtime:
            elapsed = time.perf_counter() - start
            if elapsed < config.dt:
                time.sleep(config.dt - elapsed)

    return stats
