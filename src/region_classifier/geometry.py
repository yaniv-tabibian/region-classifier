"""Geometry primitives: region shapes and shortest-distance-to-boundary.

The classifier only ever consumes distances. These shapes additionally expose
``contains()`` and ``inradius``:

* ``contains()`` is ground truth, used only by the simulator to validate the
  classifier (never by the classifier itself).
* ``inradius`` (radius of the largest inscribed circle) is the maximum distance
  an interior point can have to the boundary. The classifier uses it as a
  "half-width" anchor: ``dist > inradius`` proves the sensor is outside that
  region, which makes classification self-correcting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot

Point = tuple[float, float]


def _point_segment_distance(
    px: float, py: float, ax: float, ay: float, bx: float, by: float
) -> float:
    """Shortest distance from point (px,py) to segment (ax,ay)-(bx,by)."""
    dx, dy = bx - ax, by - ay
    if dx == 0.0 and dy == 0.0:
        return hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return hypot(px - (ax + t * dx), py - (ay + t * dy))


@dataclass(frozen=True)
class Circle:
    cx: float
    cy: float
    r: float

    def distance_to_boundary(self, x: float, y: float) -> float:
        return abs(hypot(x - self.cx, y - self.cy) - self.r)

    def contains(self, x: float, y: float) -> bool:
        return hypot(x - self.cx, y - self.cy) < self.r

    @property
    def inradius(self) -> float:
        return self.r

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (self.cx - self.r, self.cy - self.r, self.cx + self.r, self.cy + self.r)

    @property
    def centroid(self) -> Point:
        return (self.cx, self.cy)


@dataclass(frozen=True)
class Rectangle:
    """Axis-aligned rectangle given by centre and full width/height."""

    cx: float
    cy: float
    w: float
    h: float

    def distance_to_boundary(self, x: float, y: float) -> float:
        dx = abs(x - self.cx) - self.w / 2.0
        dy = abs(y - self.cy) - self.h / 2.0
        if dx <= 0.0 and dy <= 0.0:  # inside: distance to nearest edge
            return min(-dx, -dy)
        return hypot(max(dx, 0.0), max(dy, 0.0))  # outside/on: distance to perimeter

    def contains(self, x: float, y: float) -> bool:
        return abs(x - self.cx) < self.w / 2.0 and abs(y - self.cy) < self.h / 2.0

    @property
    def inradius(self) -> float:
        return min(self.w, self.h) / 2.0

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (
            self.cx - self.w / 2,
            self.cy - self.h / 2,
            self.cx + self.w / 2,
            self.cy + self.h / 2,
        )

    @property
    def centroid(self) -> Point:
        return (self.cx, self.cy)


@dataclass(frozen=True)
class Polygon:
    """Simple polygon (convex or concave) given by ordered vertices."""

    vertices: tuple[Point, ...]
    _inradius: float = field(default=-1.0, compare=False, repr=False)

    def __post_init__(self) -> None:
        if len(self.vertices) < 3:
            raise ValueError("polygon needs at least 3 vertices")
        object.__setattr__(self, "_inradius", self._compute_inradius())

    def _edges(self):
        v = self.vertices
        for i in range(len(v)):
            yield v[i], v[(i + 1) % len(v)]

    def distance_to_boundary(self, x: float, y: float) -> float:
        return min(
            _point_segment_distance(x, y, ax, ay, bx, by)
            for (ax, ay), (bx, by) in self._edges()
        )

    def contains(self, x: float, y: float) -> bool:
        # ray casting
        v = self.vertices
        inside = False
        j = len(v) - 1
        for i in range(len(v)):
            xi, yi = v[i]
            xj, yj = v[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside

    def _compute_inradius(self, grid: int = 80) -> float:
        xmin, ymin, xmax, ymax = self.bounds
        best = 0.0
        for i in range(grid):
            x = xmin + (xmax - xmin) * (i + 0.5) / grid
            for k in range(grid):
                y = ymin + (ymax - ymin) * (k + 0.5) / grid
                if self.contains(x, y):
                    best = max(best, self.distance_to_boundary(x, y))
        return best

    @property
    def inradius(self) -> float:
        return self._inradius

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        xs = [p[0] for p in self.vertices]
        ys = [p[1] for p in self.vertices]
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def centroid(self) -> Point:
        n = len(self.vertices)
        return (
            sum(p[0] for p in self.vertices) / n,
            sum(p[1] for p in self.vertices) / n,
        )


@dataclass
class RegionField:
    """The two regions the sensor lives in. Provides the distances the sensor
    reports and the ground-truth label used only for validation."""

    region_a: Circle | Rectangle | Polygon
    region_b: Circle | Rectangle | Polygon

    def dist_a(self, x: float, y: float) -> float:
        return self.region_a.distance_to_boundary(x, y)

    def dist_b(self, x: float, y: float) -> float:
        return self.region_b.distance_to_boundary(x, y)

    def true_label(self, x: float, y: float) -> str:
        if self.region_a.contains(x, y):
            return "In A"
        if self.region_b.contains(x, y):
            return "In B"
        return "Outside"
