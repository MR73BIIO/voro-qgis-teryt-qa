# Results for v0.2 (C7, state border)

Prediction: [`PREDICTION_v0.2.md`](../PREDICTION_v0.2.md), commit `a360ea1`, written before the code of C7.
Code of C7: commit `e8f6d2e`. Reference: voro-gis-qa commit `544fbec`, run again on 2026-10-24.

Measured on 2026-10-24 in QGIS 3.44.15 on Windows (GEOS 3.15), with the layers `panstwo` (state border)
and `known_uncovered` (the sea) of the voro-gis-qa golden dataset. Script: [`scripts/measure_v0_2.py`](../scripts/measure_v0_2.py).

## Predictions

| Prediction | Result | |
|---|---|---|
| P4: golden dataset gives no findings, sea exception used once, C6 exception once, PASS | 0 findings, `c7_known_exceptions_applied` 1, `c6_known_exceptions_applied` 1, PASS | holds |
| P5: C1–C6 do not change; without the state layer the result is as in 0.1.1 | pairs C1–C6 identical with voro-gis-qa on golden, `seed_42` and `seed_9`. `seed_42` without the state layer: 2335 findings, 0 of them C7, C7 skipped in the diagnostics | holds |
| P6: 20 gaps cut at the state border (`seed_9`, E9) all found, 0 C7 false alarms | E9 20 of 20 found; C7: 20 true, 0 missed, 0 false alarms (`evaluate.py` of voro-gis-qa) | holds |
| P7: pairs (check, TERYT) of C7 identical with voro-gis-qa | golden 0 = 0, `seed_42` 1752 = 1752, `seed_9` 20 = 20, identical | holds |
| P8: a hole at the coast stays local | test `test_coastal_gap_stays_local` passes in QGIS 3.40, 3.44 and 4.2 | holds |

## Numbers

| Dataset | C7 plugin | C7 voro-gis-qa | Pieces at the border | Below 150 m² | Largest below 150 m² (plugin / voro-gis-qa) | Sea exception | Time |
|---|---|---|---|---|---|---|---|
| golden | 0 | 0 | 7418 | 7417 | 73.591028 / 73.591028 m² | 1 | 53 s |
| `seed_42` | 1752 | 1752 | 8324 | 7551 | 149.691228 / 149.691228 m² | 1 | 76 s |
| `seed_9` | 20 | 20 | 7438 | 7417 | 73.591028 / 73.591028 m² | 1 | 72 s |
| `seed_42`, no state layer | 0 | – | – | – | – | – | 71 s |

The pieces include the sea as one reference piece.

## Close to the threshold

On `seed_42` one piece has 149.69 m², 0.31 m² under the threshold of 150 m². This was written down before the run as a risk for P7: if QGIS and Shapely gave a slightly different area, the piece could cross the threshold. They give the same area to about 0.000000001 m², and the piece stays below the threshold in both tools.

## What did not change

The only known difference from 0.1 is still there and is still only in the diagnostics of C5: [`differences.md`](differences.md), point 1. C7 adds no difference.
