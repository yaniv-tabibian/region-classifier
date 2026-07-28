"""Optional stress test — end-to-end accuracy on many RANDOM 2-D scenarios.

Case 2 = two separated circles (a gap between them); Case 1 = two adjacent
rectangles sharing an edge. Deterministic (fixed seed). The residual < a few %
is the inherent one-sample latency at boundary crossings, not wrong-branch
errors. Delete tests/stress/ to remove.
"""

import random

from region_classifier.config import SimConfig
from region_classifier.simulator import run

MIN_ACC = 0.95
MEAN_ACC = 0.98
_rng = random.Random(20260728)


def _case2(seed):
    while True:
        rA = round(_rng.uniform(4, 10), 2)
        rB = round(_rng.uniform(4, 10), 2)
        cA = (round(_rng.uniform(-35, 35), 1), round(_rng.uniform(-35, 35), 1))
        cB = (round(_rng.uniform(-35, 35), 1), round(_rng.uniform(-35, 35), 1))
        if ((cA[0] - cB[0]) ** 2 + (cA[1] - cB[1]) ** 2) ** 0.5 > rA + rB + 2:
            break
    return SimConfig.from_dict(
        dict(
            seed=seed,
            dt=0.1,
            duration_s=120,
            pasture=dict(xmin=-50, ymin=-50, xmax=50, ymax=50),
            regions=dict(
                A=dict(type="circle", center=list(cA), radius=rA),
                B=dict(type="circle", center=list(cB), radius=rB),
            ),
            motion=dict(
                mean_speed=round(_rng.uniform(2, 4), 1), speed_sigma=1.5, turn_sigma=0.4
            ),
        )
    )


def _case1(seed):
    wa = round(_rng.uniform(8, 20), 1)
    wb = round(_rng.uniform(8, 20), 1)
    h = round(_rng.uniform(20, 40), 1)
    return SimConfig.from_dict(
        dict(
            seed=seed,
            dt=0.1,
            duration_s=120,
            pasture=dict(xmin=-60, ymin=-40, xmax=60, ymax=40),
            regions=dict(
                A=dict(type="rectangle", center=[-wa / 2, 0], width=wa, height=h),
                B=dict(type="rectangle", center=[wb / 2, 0], width=wb, height=h),
            ),
            motion=dict(
                mean_speed=round(_rng.uniform(2, 4), 1), speed_sigma=1.5, turn_sigma=0.4
            ),
        )
    )


def _accuracies(builder, base, n):
    accs = []
    for s in range(n):
        stats = run(builder(base + s), realtime=False, validate=True)
        assert stats.ticks > 200
        accs.append(stats.accuracy)
    return accs


def test_case2_random_scenarios():
    accs = _accuracies(_case2, 1000, 8)
    assert min(accs) >= MIN_ACC, accs
    assert sum(accs) / len(accs) >= MEAN_ACC, accs


def test_case1_random_scenarios():
    accs = _accuracies(_case1, 5000, 6)
    assert min(accs) >= MIN_ACC, accs
    assert sum(accs) / len(accs) >= MEAN_ACC, accs
