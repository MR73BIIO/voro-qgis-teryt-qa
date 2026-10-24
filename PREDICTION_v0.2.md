# Prediction for v0.2 (written before the C7 code)

Date: 2026-10-24. Base: plugin v0.1.1 (C1–C6 do not change).
Source of C7: [voro-gis-qa](https://github.com/MR73BIIO/voro-gis-qa), commit 544fbec: `scripts/measures.py` (state border part), `scripts/checks.py` (`c7_border`), `docs/prediction_1.6_border.md`, `docs/note_1.6_design_change.md`, `tests/test_border.py`.

## What v0.2 adds

C7, coverage of the state border, with the same rule as voro-gis-qa:

- Every piece of the state layer without a municipality, and every piece of a municipality outside the state layer, larger than 150 m2 (`c7_border_tol_m2`) is a finding, severity high. It is reported for every municipality that touches the piece (1 m buffer), or for the whole dataset when no municipality touches it.
- The known area without municipalities (the sea) is one reference piece. It is accepted only when its area matches the known exception (8,776,989,565 m2, tolerance 1 m2). If not, one finding for the whole dataset.
- C7 runs only when the CRS is right, like C3 and C5.

Two new optional inputs:

| Input | What it is | Without it |
|---|---|---|
| State border layer | PRG `A00_Granice_panstwa` | C7 is skipped and the diagnostics say so. C1–C6 work as in v0.1.1. |
| Known uncovered areas | reference layer, e.g. `known_uncovered` from the golden dataset | The sea is an ordinary uncovered piece, matched with the exception by area only. This is the first design of voro-gis-qa: it works on clean data, but a hole at the coast makes the whole coast reported (note_1.6). The help text says to give this layer. |

Both layers are transformed to the expected CRS (EPSG:2180) before measuring.

Thresholds and exceptions: no new numbers. `params.json` and `known_exceptions.json` of the plugin already contain `c7_border_tol_m2` and the sea exception, unchanged from voro-gis-qa.

## Known limitation (written down before the code)

The sea exception is an area measured on one PRG edition (the one in `manifest.json` of voro-gis-qa). On another PRG edition the sea area will be different, and C7 gives one finding: the known uncovered area has a different area. This is the rule working as designed, not a bug. Building the reference layer and the exception for any PRG edition is not part of v0.2.

## Predictions

Numbering continues from v0.1 (P1–P3). Runs use the layers `panstwo` and `known_uncovered` from `golden.gpkg` as the state layer and the reference layer.

**P4. Golden dataset.** With the state layer and the reference layer: 0 findings in total (C1–C7), the sea exception applied exactly once, the C6 exception applied exactly once, status PASS.

**P5. C1–C6 do not change.** On the golden dataset and on `seed_42` the pairs (check, TERYT) of C1–C6 are identical to v0.1.1. Without the state layer the whole result is identical to v0.1.1.

**P6. Gaps at the state border.** On the E9 set of voro-gis-qa (seed 9, 20 gaps cut at the state border) the plugin finds 20 of 20 with C7 and gives 0 C7 false alarms, the same result as voro-gis-qa.

**P7. Same answers as voro-gis-qa.** On the golden dataset, on `seed_42` and on the E9 set the set of pairs (check, TERYT) for C7 is identical to `run_checks.py` of voro-gis-qa. Only pairs are compared, not the text of `detail` and not areas.

**P8. A hole at the coast stays local.** The synthetic test of voro-gis-qa (`test_coastal_gap_stays_local`) runs in the plugin tests in QGIS: the damaged municipality is reported, at most 3 municipalities get C7, and the sea exception is applied once.

## What each result means

- P4 to P8 all hold: the port of C7 is faithful. v0.2 can be released.
- P4 fails: the plugin raises alarms on clean data. If the cause is the sea area differing by more than 1 m2 between GEOS in QGIS and Shapely, it is written down in `docs/differences.md` with the measured difference. The tolerance is not changed to make the test pass.
- P5 fails: C7 broke something that worked. Fixed before anything else.
- P6 fails (fewer than 20 or any C7 false alarm): every miss and every false alarm is listed with its TERYT and explained. No release until it is explained.
- P7 fails but P4 to P6 hold: each different pair is described in `docs/differences.md` with the reason, as in v0.1.
- P8 fails: the design change from note_1.6 was not ported correctly. Fixed before release.

The results of voro-gis-qa are the reference. They are not changed to fit the plugin.
