# Prediction for v0.1 (written before any plugin code)

Date: 2026-10-22. Source of the checks: [voro-gis-qa](https://github.com/MR73BIIO/voro-gis-qa), commit 544fbec.

## What v0.1 will do

One QGIS Processing algorithm. Input: municipalities layer (gminy), counties layer (powiaty), TERC file (CSV). Output: a layer of findings, one row per finding, with the fields `check`, `teryt`, `severity`, `detail`.

Checks in v0.1, the same rules as in voro-gis-qa:

| Check | What it looks at | Severity |
|---|---|---|
| C1 | empty or invalid geometry | critical |
| C2 | TERYT format, duplicates, municipality type 1/2/3 | critical |
| C3 | municipality inside its own county | critical |
| C4 | declared CRS, geometry inside the extent of Poland | critical |
| C5 | overlaps and gaps between municipalities | high |
| C6 | name present and equal to TERC | medium |

Not in v0.1: C7 (state border, needs the sea as a reference layer), incidents, report. C7 goes to v0.2.

Thresholds and known exceptions are taken without change from `params.json` and `known_exceptions.json` of voro-gis-qa. The plugin does not get its own thresholds.

## Predictions

**P1. Golden dataset.** On the golden dataset (2479 municipalities, 380 counties) the plugin returns 0 findings, and the one known C6 exception is applied exactly once.

**P2. Seed 42.** On `seed_42` (E1–E8, 20 errors of each type, 160 errors in total) the plugin finds 160 of 160 with the expected check and gives 0 false alarms, the same result as voro-gis-qa.

**P3. Same answers as voro-gis-qa.** On the golden dataset and on `seed_42` the set of pairs (check, TERYT) from the plugin is identical to the set from `run_checks.py` without C7. Only pairs are compared, not the text of `detail`, because QGIS and Shapely can describe the same invalid geometry in different words.

## What each result means

- P1, P2 and P3 all hold: the port is faithful. v0.1 can be released.
- P1 fails: the plugin raises alarms on clean data. This is a bug in the port. It is fixed before anything else, and thresholds are not touched.
- P2 fails (fewer than 160 or any false alarm): every miss and every false alarm is listed with its TERYT and explained. No release until it is explained.
- P3 fails but P1 and P2 hold: each different pair is described in `docs/differences.md` with the reason. A difference is allowed only when the cause is known and written down.

The results of voro-gis-qa are the reference. They are not changed to fit the plugin.
