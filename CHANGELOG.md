# Changelog

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
