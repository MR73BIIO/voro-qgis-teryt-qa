# voro-qgis-teryt-qa

QGIS plugin for quality checks of Polish administrative boundaries (PRG) against the official TERC register.

The checks come from [voro-gis-qa](https://github.com/MR73BIIO/voro-gis-qa), where they were built and measured in Python. This repository moves them into QGIS as a Processing algorithm: *VORO TERYT QA → Check boundaries against TERC*.

## What it checks

| Check | What it looks at | Severity |
|---|---|---|
| C1 | empty or invalid geometry | critical |
| C2 | TERYT format, duplicates, municipality type 1/2/3 | critical |
| C3 | municipality inside its own county | critical |
| C4 | declared CRS, geometry inside the extent of Poland | critical |
| C5 | overlaps and gaps between municipalities | high |
| C6 | name present and equal to TERC | medium |

Output: a layer with one row per finding (check, TERYT, severity, detail), with the geometry of the municipality, so the errors can be seen on the map. Thresholds and the known exception come from voro-gis-qa (`params.json`, `known_exceptions.json`).

Not yet: C7 (state border), report, translations.

## Status

Version 0.0.3, tested in QGIS 3.44.15 on Windows. Results against the prediction written before the code (`PREDICTION.md`):

- **P1, golden dataset** (2479 municipalities, 380 counties): 0 findings, status PASS, the known C6 exception applied once. 7075 pairs of municipalities checked for overlaps, the same number as in voro-gis-qa.
- **P2, `seed_42`** (160 injected errors, 20 of each type E1–E8): 160 of 160 found with the expected check, 0 false alarms. Scored with `evaluate.py` from voro-gis-qa.
- **P3, same answers:** 2335 pairs (check, TERYT) on `seed_42`, identical to voro-gis-qa. Compared with `scripts/compare_parity.py`. One difference in the diagnostics, without effect on findings, is described in `docs/differences.md`.

Run time on the full layer: about 60 seconds.

Two things learned on the way: Processing stops on invalid geometries by default, so the plugin switches that filter off for its own read (a QA tool has to see them). And the algorithm must not be run with "iterate over this layer", because overlaps, gaps and duplicates only exist between municipalities.

## License

GPL-2.0-or-later, as required for plugins in the official QGIS repository.

---

Marcin Ruszczak · MR73BIIO · Polish, German, Russian, English
