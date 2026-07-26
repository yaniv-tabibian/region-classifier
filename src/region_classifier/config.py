"""Configuration loading and validation.

Region sizes and shapes come from an external YAML file (never from script
constants), satisfying the assignment's configurability requirement. Ships with
a small schema check that raises clear errors on bad input.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .geometry import Circle, Polygon, Rectangle
from .motion import MotionParams

Shape = Circle | Rectangle | Polygon


def shape_from_dict(spec: dict[str, Any]) -> Shape:
    if not isinstance(spec, dict) or "type" not in spec:
        raise ValueError(f"region spec must be a mapping with a 'type': {spec!r}")
    t = str(spec["type"]).lower()
    try:
        if t == "circle":
            return Circle(
                float(spec["center"][0]),
                float(spec["center"][1]),
                float(spec["radius"]),
            )
        if t == "rectangle":
            return Rectangle(
                float(spec["center"][0]),
                float(spec["center"][1]),
                float(spec["width"]),
                float(spec["height"]),
            )
        if t == "polygon":
            pts = tuple((float(x), float(y)) for x, y in spec["points"])
            return Polygon(pts)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ValueError(f"invalid {t} spec {spec!r}: {exc}") from exc
    raise ValueError(f"unknown region type {t!r} (use circle/rectangle/polygon)")


@dataclass
class SimConfig:
    seed: int
    dt: float
    duration_s: float
    pasture: tuple[float, float, float, float]
    region_a: Shape
    region_b: Shape
    motion: MotionParams
    distance_noise_std: float
    smoothing: float
    waypoints: list[tuple[float, float]]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimConfig:
        try:
            regions = data["regions"]
            region_a = shape_from_dict(regions["A"])
            region_b = shape_from_dict(regions["B"])
            p = data["pasture"]
            pasture = (
                float(p["xmin"]),
                float(p["ymin"]),
                float(p["xmax"]),
                float(p["ymax"]),
            )
        except KeyError as exc:
            raise ValueError(f"missing required config key: {exc}") from exc

        dt = float(data.get("dt", 0.1))
        if dt <= 0:
            raise ValueError("dt must be > 0")
        duration = float(data.get("duration_s", 120.0))
        if duration <= 0:
            raise ValueError("duration_s must be > 0")

        motion_d = data.get("motion", {}) or {}
        motion = MotionParams(**{k: float(v) for k, v in motion_d.items()})

        wps = data.get("waypoints")
        if wps:
            waypoints = [(float(x), float(y)) for x, y in wps]
        else:  # default cycle: A -> outside -> B -> outside
            waypoints = [
                region_a.centroid,
                (pasture[0] + 1.0, pasture[3] - 1.0),
                region_b.centroid,
                (pasture[2] - 1.0, pasture[1] + 1.0),
            ]

        return cls(
            seed=int(data.get("seed", 0)),
            dt=dt,
            duration_s=duration,
            pasture=pasture,
            region_a=region_a,
            region_b=region_b,
            motion=motion,
            distance_noise_std=float(data.get("noise", {}).get("distance_std", 0.0)),
            smoothing=float(data.get("smoothing", 0.0)),
            waypoints=waypoints,
        )

    @classmethod
    def load(cls, path: str | Path) -> SimConfig:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"config not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            raise ValueError(f"config {path} must be a YAML mapping")
        return cls.from_dict(data)
