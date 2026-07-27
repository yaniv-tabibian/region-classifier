# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-07-27
### Added
- Real-time simulation: 2D correlated-random-walk motion with variable
  (Ornstein–Uhlenbeck) speed, feeding a sensor that exposes only
  `get_dist_a()` / `get_dist_b()`.
- Online region classifier (In A / In B / Outside): half-width anchors +
  adaptive boundary-crossing detection, O(1) per sample, no post-processing.
- Configurable regions (circle / rectangle / polygon) via external YAML;
  a bundled default scenario so `region-sim` runs with no arguments.
- CLI `region-sim` with live console output, `--validate`, optional
  matplotlib view / GIF export, and `--version`.
- Test suite (geometry, classifier, config, end-to-end accuracy) and
  GitHub Actions CI (lint + type-check + tests on Python 3.10–3.12).
