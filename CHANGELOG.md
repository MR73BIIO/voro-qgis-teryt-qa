# Changelog

## 0.2.0 · 2026-10-24

- New check C7, state border (high): pieces of Poland without a municipality and parts of municipalities outside Poland larger than 150 m2 (`c7_border_tol_m2`). Rule, threshold and the sea exception from voro-gis-qa, unchanged.
- Two new optional inputs: *State border* (PRG `A00_Granice_panstwa`) and *Known areas without municipalities* (the sea, one reference piece). Without the state layer C7 is skipped and the result is the same as in 0.1.1.
- HTML report: row, diagnostics and threshold of C7, names of the new input layers.
- Measured against the prediction written before the code (`PREDICTION_v0.2.md`): golden dataset 0 findings with the sea exception used once; `seed_9` 20 of 20 gaps at the state border found, 0 false alarms; 1752 of 1752 C7 pairs identical with voro-gis-qa on `seed_42`. Details: `docs/results_v0.2.md`.
- Known limitation: the area of the sea was measured on one PRG edition; with another edition C7 gives one finding for the whole dataset.

## 0.1.1 · 2026-10-24

- Report status texts are built from pairs, so the plugins.qgis.org security scan (Bandit B105) no longer reads the `PASS` status as a password. Same texts, same report.
- Removed the deprecated `supportsQt6` flag from `metadata.txt`; QGIS 4 support comes from `qgisMaximumVersion=4.99`.
- No change to checks C1-C6, rules or thresholds.

## 0.1.0 · 2026-10-22

First release.

- Processing algorithm *Check boundaries against TERC* with checks C1–C6: geometry, TERYT code, municipality inside its own county, CRS and extent of Poland, overlaps and gaps, name against TERC.
- Rules, thresholds and the known exception come from voro-gis-qa, unchanged.
- Output: a layer of findings with the geometry of the municipality. Optional HTML report in Polish.
- Interface in Polish and English, depending on the language of QGIS.
- Measured against the prediction written before the code (`PREDICTION.md`): golden dataset 0 findings; `seed_42` 160 of 160 injected errors found, 0 false alarms; 2335 of 2335 pairs identical with voro-gis-qa.
- Automatic tests in QGIS 3.40, 3.44 and 4.2.
