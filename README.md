# region-classifier

[![CI](https://github.com/OWNER/region-classifier/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/region-classifier/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

> Replace `OWNER` in the CI badge above with your GitHub username after you push.

Real-time classification of a moving GPS sensor as **In A**, **In B**, or
**Outside**, using only the two *shortest-distance-to-boundary* streams
`get_dist_a()` and `get_dist_b()` — no position is ever given to the classifier.

![live demo](examples/demo.gif)

The sensor wanders through a 2D world containing two disjoint regions. At each
tick it reports its distance to each region's boundary; the classifier decides
the current region **online**, with no post-processing of the trajectory.

---

## Why it is not trivial

A single distance-to-boundary reading is **ambiguous**: being 3 m *inside* a
region and 3 m *outside* it both read `3`. The decision therefore has to be
recovered over time. Two ideas do it (see [`classifier.py`](src/region_classifier/classifier.py)):

1. **Half-width anchors.** An interior point of a region is at most `inradius`
   from its boundary, so `dist > inradius` *proves* the sensor is outside that
   region. This is certain from a single sample and makes the classifier
   **self-correcting** — it can never get permanently stuck in a wrong state.
2. **Boundary-crossing detection.** A crossing is the moment a distance dips to
   ~0 and rebounds; each crossing toggles that region's membership. The
   near-zero threshold is **adaptive** — it tracks the recent `|Δdistance|`
   (≈ speed·dt), so it self-scales with the sensor's non-constant speed.

The algorithm is causal and **O(1)** in time and memory per sample.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[viz,dev]"     # 'viz' adds matplotlib, 'dev' adds test/lint tools
```

(Or `make install`. A `Makefile` wraps the common tasks: `make run`, `make test`,
`make lint`, `make format`, `make demo`.)

## Quick start (zero config)

```bash
region-sim            # runs a bundled default scenario, live in the console
region-sim --version
```

## Run

```bash
# runs with no arguments using the bundled default scenario
region-sim

# a specific scenario, checked every tick against ground truth
region-sim --config configs/two_circles.yaml --no-realtime --validate

# same, but check every tick against ground truth and print accuracy
region-sim --config configs/two_circles.yaml --no-realtime --validate

# live map (needs the viz extra), or render a GIF headless
region-sim --config configs/adjacent_bands.yaml --plot
region-sim --config configs/two_circles.yaml --save-gif examples/demo.gif --duration 30
```

Sample output:

```
t=  41.2s  d_a=  0.13  d_b= 22.90  ->  In A      (truth: In A     OK)
t=  55.7s  d_a= 18.40  d_b=  0.09  ->  In B      (truth: In B     OK)
accuracy vs ground truth: 99.57% over 3000 ticks
```

The remaining <0.5% are the one-sample transients at the instant of a crossing —
inherent to a causal decision from unsigned distances.

## Configuration (sizes & shapes are external, not constants)

Scenarios are YAML files under [`configs/`](configs). Regions may be `circle`,
`rectangle`, or `polygon`, of any size and position:

```yaml
seed: 42
dt: 0.1
duration_s: 120
pasture: {xmin: -40, ymin: -40, xmax: 40, ymax: 40}
regions:
  A: {type: circle,    center: [-15, 10], radius: 9}
  B: {type: rectangle, center: [16, -8], width: 12, height: 10}
motion: {mean_speed: 3.0, speed_sigma: 1.5, turn_sigma: 0.4}
noise:  {distance_std: 0.0}
```

* `configs/two_circles.yaml` — two disjoint circles with an Outside gap.
* `configs/adjacent_bands.yaml` — two rectangles that **share an edge**
  (direct A↔B transitions).

## How the simulation is wired

```
config (YAML) ─▶ geometry (shapes) ─┐
                                     ├─▶ Sensor  ─get_dist_a()/get_dist_b()─▶ RegionClassifier ─▶ label
config (YAML) ─▶ motion (var speed) ─┘  (hides position)                        (online, O(1))
```

* [`geometry.py`](src/region_classifier/geometry.py) — shapes + distance-to-boundary + `inradius`.
* [`motion.py`](src/region_classifier/motion.py) — correlated random walk with Ornstein–Uhlenbeck (variable) speed.
* [`sensor.py`](src/region_classifier/sensor.py) — hides the true position; exposes only the two getters.
* [`classifier.py`](src/region_classifier/classifier.py) — the online classifier.
* [`simulator.py`](src/region_classifier/simulator.py) — the real-time loop.

## Tests

```bash
pytest            # 16 tests: geometry, classifier (crafted streams), config, end-to-end accuracy
ruff check . && mypy && black --check .
```

The classifier is tested in isolation on hand-crafted distance streams
(enter/leave, adjacent A↔B via a shared edge, grazes that must not toggle,
anchor self-correction), plus an end-to-end run asserting ≥95% accuracy.

## License

MIT — see [LICENSE](LICENSE).
