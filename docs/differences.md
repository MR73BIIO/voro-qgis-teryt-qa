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

## 3. C7, state border (v0.2): no difference

Checked on 2026-10-24 with the plugin from branch v0.2 (QGIS 3.44.15, GEOS 3.15) against voro-gis-qa 544fbec.
The pairs (check, TERYT) of C7 are identical on the golden dataset (0 = 0), `seed_42` (1752 = 1752) and `seed_9` (20 = 20).
The diagnostics of C7 are the same: number of pieces, pieces below the threshold, sea exception used once.
The largest piece below the threshold differs only in the ninth digit (golden: 73.59102821 m² in the plugin,
73.59102822 m² in voro-gis-qa). The piece of 149.69 m² on `seed_42`, 0.31 m² under the threshold, has the same
area in both tools and stays below the threshold. Point 1 above is still the only difference.
