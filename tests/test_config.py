from pathlib import Path

import pytest

from region_classifier.config import SimConfig, shape_from_dict
from region_classifier.geometry import Circle, Rectangle

CONFIGS = Path(__file__).resolve().parents[1] / "configs"


def test_bundled_default_config_loads():
    cfg = SimConfig.load_default()
    assert cfg.dt > 0 and cfg.duration_s > 0
    assert cfg.region_a.inradius > 0 and cfg.region_b.inradius > 0


def test_shape_factory():
    c = shape_from_dict({"type": "circle", "center": [1, 2], "radius": 3})
    assert isinstance(c, Circle) and c.r == 3
    r = shape_from_dict(
        {"type": "rectangle", "center": [0, 0], "width": 4, "height": 6}
    )
    assert isinstance(r, Rectangle) and r.inradius == 2


def test_bad_shape_raises():
    with pytest.raises(ValueError):
        shape_from_dict({"type": "hexagon", "center": [0, 0]})
    with pytest.raises(ValueError):
        shape_from_dict({"center": [0, 0], "radius": 1})  # missing type


def test_shipped_configs_load():
    for name in ("two_circles.yaml", "adjacent_bands.yaml"):
        cfg = SimConfig.load(CONFIGS / name)
        assert cfg.dt > 0 and cfg.duration_s > 0
        assert cfg.region_a.inradius > 0 and cfg.region_b.inradius > 0
        assert len(cfg.waypoints) >= 1


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        SimConfig.load(CONFIGS / "does_not_exist.yaml")
