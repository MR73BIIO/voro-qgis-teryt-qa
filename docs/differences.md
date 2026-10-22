# Known differences between the plugin and voro-gis-qa

Reference: voro-gis-qa commit 544fbec. Plugin version 0.0.3, QGIS 3.44.15 (GEOS 3.15.0).

The prediction (P3 in `PREDICTION.md`) allows a difference only when its cause is known and written down here.

## 1. Number of overlaps below the threshold (diagnostics only)

| | plugin | voro-gis-qa |
|---|---|---|
| `c5_overlaps_below_tol` on `seed_42` | 2 | 3 |
| `c5_overlap_max_below_tol_m2` on `seed_42` | 5.96e-08 | 6.25e-08 |

**Effect on findings: none.** These are overlaps of about 0.00000006 m2 on shared edges of municipalities. The threshold is 1 m2, so neither tool reports them. The pairs (check, TERYT) are identical: 2335 of 2335.

**Cause.** The intersection of two polygons that share an edge is computed in floating point. For one pair Shapely returns a sliver with area slightly above 0, QGIS returns area 0. Both use GEOS, but through different bindings and possibly different GEOS versions, so the last digits of such slivers can differ.

**Decision.** Not changed. The number of checked pairs (6852), gaps (888), gaps below the threshold (14) and the largest gap below the threshold (0.836 m2) are the same in both tools.

## 2. Text of `detail` for invalid geometry (C1)

The reason for an invalid geometry is written by QGIS, not by Shapely, so the wording can differ. The prediction compares only pairs (check, TERYT), not this text.
