"""End-to-end: run the real simulation headless and check the online classifier
matches ground truth almost everywhere (mismatches only in the brief crossing
transients)."""

from pathlib import Path

from region_classifier.config import SimConfig
from region_classifier.simulator import run

CONFIGS = Path(__file__).resolve().parents[1] / "configs"


def _accuracy(name: str) -> float:
    cfg = SimConfig.load(CONFIGS / name)
    cfg.duration_s = 200.0
    stats = run(cfg, realtime=False, validate=True)
    assert stats.ticks > 500
    return stats.accuracy


def test_two_circles_accuracy():
    assert _accuracy("two_circles.yaml") >= 0.95


def test_adjacent_bands_accuracy():
    assert _accuracy("adjacent_bands.yaml") >= 0.95


def test_run_is_deterministic():
    cfg = SimConfig.load(CONFIGS / "two_circles.yaml")
    cfg.duration_s = 40.0
    a = run(cfg, realtime=False, validate=True).accuracy
    b = run(cfg, realtime=False, validate=True).accuracy
    assert a == b
