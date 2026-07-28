"""Optional stress test — the half-width ANCHOR invariant.

Guarantee under test: after any update, the classifier never claims membership
of a region it is provably outside of. Concretely, for every tick:
  * label == "In A"  =>  d_a <= inradius_a + margin
  * label == "In B"  =>  d_b <= inradius_b + margin
  * never "In A" and "In B" simultaneously.
This is the "no valid value enters a wrong branch" property, brute-forced over
many random distance streams. Delete tests/stress/ to remove.
"""

import random

from region_classifier.classifier import RegionClassifier


def test_anchor_invariant_bruteforce():
    rng = random.Random(20260728)  # fixed seed -> deterministic
    violations = checks = 0
    for _ in range(1200):
        ra = rng.uniform(1, 10)
        rb = rng.uniform(1, 10)
        margin = rng.choice([0.0, 0.5, 2.0])
        clf = RegionClassifier(inradius_a=ra, inradius_b=rb, anchor_margin=margin)
        d_a = rng.uniform(0, 25)
        d_b = rng.uniform(0, 25)
        for _ in range(40):
            d_a = max(0.0, d_a + rng.uniform(-3, 3))
            d_b = max(0.0, d_b + rng.uniform(-3, 3))
            label = clf.update(d_a, d_b)
            checks += 1
            if label == "In A" and d_a > ra + margin + 1e-9:
                violations += 1
            if label == "In B" and d_b > rb + margin + 1e-9:
                violations += 1
    assert checks > 40000
    assert violations == 0


def test_far_outside_is_always_outside():
    clf = RegionClassifier(inradius_a=5, inradius_b=4)
    # both distances well beyond the inradii -> must be Outside, no history helps
    for d in (6.0, 20.0, 100.0):
        assert clf.update(d, d) == "Outside"


def test_deep_inside_A_then_leaving_is_anchored_out():
    clf = RegionClassifier(inradius_a=5, inradius_b=5)
    # enter A (dip to ~0 then rise) ...
    for d_a in (10, 6, 2, 0.05, 1.0):
        clf.update(d_a, 12)
    assert clf.label == "In A"
    # ... then jump far outside A -> anchor forces Outside regardless of history
    assert clf.update(20.0, 12.0) == "Outside"
