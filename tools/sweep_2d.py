"""Randomised large-scale sweep of the SHIPPED 2-D classifier.

The other two harnesses in this folder verify the 1-D reference *rule*. This one
exercises the real pipeline -- RegionField (circle / rectangle / polygon) -> Sensor
-> RegionClassifier -- over randomised geometries in both configurations
(adjacent and separated), with randomised motion, dt, and distance noise.

Two things it is careful about, because both were found to matter:

1. SAMPLING REGIME. Crossing detection needs the boundary dip to actually be
   sampled. The dimensionless control is step-per-tick / inradius = speed*dt/r.
   The shipped configs sit near 0.03. Pushed to ~0.2 the GROUND TRUTH itself
   flips every couple of ticks, and a causal detector -- which needs a dip and a
   rebound, so >= 3 samples -- cannot track that at any accuracy. Accuracy there
   collapses to ~60%, which is a Nyquist limit, not a classifier defect. This
   sweep stays in [0.005, 0.05]; pass --ratio-max to explore past it.

2. COLD START. The classifier begins with both membership bits False (Outside),
   which matches how the simulator starts the sensor (a corner of the field).
   Cold-starting *inside* a region is a different, much slower recovery, so the
   two are reported separately rather than blended into one headline number.

Run:  python tools/sweep_2d.py [--scenarios-per-pairing N] [--ticks N]
                              [--ratio-max R] [--quick]
"""

from __future__ import annotations

import argparse
import sys

import numpy as np

from region_classifier.classifier import RegionClassifier
from region_classifier.geometry import Circle, Polygon, Rectangle, RegionField
from region_classifier.motion import CorrelatedRandomWalk, MotionParams
from region_classifier.sensor import Sensor

KINDS = ("circle", "rectangle", "polygon")


def make_shape(kind, cx, cy, size, rng):
    if kind == "circle":
        return Circle(cx, cy, size)
    if kind == "rectangle":
        return Rectangle(cx, cy, 2 * size, 2 * size * rng.uniform(0.6, 1.8))
    n = int(rng.integers(5, 9))
    ang = np.sort(rng.uniform(0.0, 2.0 * np.pi, n))
    return Polygon(tuple((cx + size * np.cos(a), cy + size * np.sin(a)) for a in ang))


def build(kind_a, kind_b, adjacent, inside_start, ratio_max, rng):
    ra, rb = rng.uniform(4.0, 12.0), rng.uniform(4.0, 12.0)
    gap = 0.0 if adjacent else rng.uniform(2.0, 12.0)
    A = make_shape(kind_a, -(ra + gap / 2), 0.0, ra, rng)
    B = make_shape(kind_b, (rb + gap / 2), 0.0, rb, rng)
    field = RegionField(A, B)
    inradius = min(A.inradius, B.inradius)
    dt = float(rng.choice([0.05, 0.1, 0.2]))
    ratio = rng.uniform(0.005, ratio_max)
    speed = ratio * inradius / dt
    pad = 12.0
    bounds = (-(ra + gap / 2) - ra - pad, -max(ra, rb) - pad,
              (rb + gap / 2) + rb + pad, max(ra, rb) + pad)
    waypoints = [A.centroid, (bounds[0] + 2, bounds[3] - 2), B.centroid,
                 (bounds[2] - 2, bounds[1] + 2)]
    walk = CorrelatedRandomWalk(
        rng, bounds, waypoints,
        MotionParams(mean_speed=speed, speed_sigma=speed * 0.4, turn_sigma=0.4),
        start=A.centroid if inside_start else None,
    )
    noise = float(rng.choice([0.0, 0.0, 0.01, 0.02]))
    sensor = Sensor(field, walk, rng, distance_noise_std=noise)
    return sensor, RegionClassifier(A.inradius, B.inradius), dt


def run_mode(inside_start, per_pairing, ticks, ratio_max, seed=20260729):
    master = np.random.default_rng(seed)
    pairings = [(a, b, adj) for a in KINDS for b in KINDS for adj in (True, False)]
    total = hits = 0
    per, lock = {}, []
    edges = {"near_boundary": 0, "exact_tie": 0, "zero_distance": 0}
    for (kind_a, kind_b, adjacent) in pairings:
        p_tot = p_ok = 0
        for _ in range(per_pairing):
            rng = np.random.default_rng(int(master.integers(0, 2**31 - 1)))
            sensor, clf, dt = build(kind_a, kind_b, adjacent, inside_start,
                                    ratio_max, rng)
            streak, locked = 0, None
            for i in range(ticks):
                sensor.step(dt)
                d_a, d_b = sensor.get_dist_a(), sensor.get_dist_b()
                truth = sensor.true_label()
                got = clf.update(d_a, d_b)
                good = got == truth
                total += 1
                p_tot += 1
                hits += good
                p_ok += good
                if locked is None:
                    streak = streak + 1 if good else 0
                    if streak >= 50:
                        locked = i
                if min(d_a, d_b) < 0.05:
                    edges["near_boundary"] += 1
                if abs(d_a - d_b) < 1e-9:
                    edges["exact_tie"] += 1
                if d_a == 0.0 or d_b == 0.0:
                    edges["zero_distance"] += 1
            lock.append(ticks if locked is None else locked)
        per[(kind_a, kind_b, adjacent)] = (p_ok, p_tot)
    return total, hits, per, np.array(lock), edges


def report(title, total, hits, per, lock, edges, ticks):
    print("=" * 78)
    print(f"  {title}")
    print("-" * 78)
    print(f"    ticks sampled     : {total:,}")
    print(f"    ACCURACY          : {100 * hits / total:.3f}%   "
          f"({total - hits:,} misses)")
    worst = min(per.items(), key=lambda kv: kv[1][0] / kv[1][1])
    print(f"    worst pairing     : {100 * worst[1][0] / worst[1][1]:.2f}%  "
          f"{worst[0][0]}/{worst[0][1]} "
          f"{'adjacent' if worst[0][2] else 'separated'}")
    print(f"    ticks to lock on  : median {int(np.median(lock))}, "
          f"p90 {int(np.percentile(lock, 90))}, "
          f"never {int((lock >= ticks).sum())}/{len(lock)}")
    print("    edge cases hit    : " + "  ".join(
        f"{k} {v:,}" for k, v in edges.items()))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenarios-per-pairing", type=int, default=30)
    ap.add_argument("--ticks", type=int, default=5000)
    ap.add_argument("--ratio-max", type=float, default=0.05,
                    help="max step-per-tick / inradius (>0.1 leaves the regime "
                         "any causal detector can track; see the module docstring)")
    ap.add_argument("--quick", action="store_true",
                    help="a fast smoke run (3 scenarios x 500 ticks per pairing)")
    args = ap.parse_args(argv)
    per_pairing = 3 if args.quick else args.scenarios_per_pairing
    ticks = 500 if args.quick else args.ticks

    print("=" * 78)
    print("SHIPPED 2-D CLASSIFIER -- randomised sweep")
    print("  18 geometry pairings (circle/rectangle/polygon squared x "
          "adjacent/separated)")
    print(f"  {per_pairing} scenarios each x {ticks:,} ticks; "
          f"step/inradius in [0.005, {args.ratio_max}]")
    for inside_start, title in (
        (False, "COLD START OUTSIDE  (matches the shipped simulator)"),
        (True, "COLD START INSIDE A (adversarial; slow-recovery case)"),
    ):
        total, hits, per, lock, edges = run_mode(
            inside_start, per_pairing, ticks, args.ratio_max)
        report(title, total, hits, per, lock, edges, ticks)
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
