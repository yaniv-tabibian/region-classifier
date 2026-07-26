"""Real-time region classification of a moving GPS sensor from
shortest-distance-to-boundary streams."""

from .classifier import RegionClassifier
from .config import SimConfig
from .geometry import Circle, Polygon, Rectangle, RegionField
from .motion import CorrelatedRandomWalk, MotionParams
from .sensor import Sensor
from .simulator import RunStats, Tick, run

__version__ = "0.1.0"

__all__ = [
    "RegionClassifier",
    "SimConfig",
    "Circle",
    "Rectangle",
    "Polygon",
    "RegionField",
    "CorrelatedRandomWalk",
    "MotionParams",
    "Sensor",
    "run",
    "Tick",
    "RunStats",
    "__version__",
]
