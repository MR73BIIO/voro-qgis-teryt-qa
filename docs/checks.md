**English** | [Polski](checks.pl.md)

# The checks, one by one

Each check below is described the way the code does it. The pictures use the same layout as the automatic tests: two counties with four municipalities each. Thresholds come from [`params.json`](../voro_teryt_qa/params.json) and are the same as in voro-gis-qa.

A municipality can have several findings. The status of the whole dataset is **REJECT** if any finding is critical, **REVIEW** if there are findings but none critical, **PASS** if there are none.

## C1 · Geometry (critical)

![C1](img/checks/c1.png)

- Empty geometry: finding "pusta geometria".
- Invalid geometry by the GEOS rules (self-intersection, ring crossing another ring, and so on): finding with the reason given by QGIS.
- Invalid municipalities are left out of C5, because overlaps and gaps cannot be measured on them. Their place shows up as a gap next to the neighbours.

## C2 · TERYT code (critical)

![C2](img/checks/c2.png)

- The code must be exactly 7 digits.
- The same code may appear only once.
- The last digit is the type of municipality and must be 1, 2 or 3 (urban, rural, urban-rural).

## C3 · Municipality inside its own county (critical)

![C3](img/checks/c3.png)

- The first 4 digits of TERYT are the county code. That county must exist in the counties layer.
- A point on the surface of the municipality must lie in that county, within 1 m (`c3_buffer_m`).

## C4 · Coordinate system and extent of Poland (critical)

![C4](img/checks/c4.png)

- The layer must be in EPSG:2180. If it is not, there is one finding for the whole dataset and C3 and C5 are skipped, because distances and areas would be meaningless.
- The bounding box of each municipality must lie inside the box of Poland (14.07–24.16 E, 49.00–54.84 N, transformed to EPSG:2180) plus 20 km (`c4_margin_m`). A municipality written in degrees inside a layer in metres ends up far away and is caught here.

## C5 · Overlaps and gaps (high)

![C5](img/checks/c5.png)

- **Overlap:** two municipalities that share more than 1 m² of area (`c5_overlap_tol_m2`). Both get a finding.
- **Gap:** a hole in the union of all municipalities larger than 1 m² (`c5_gap_tol_m2`). Every municipality within 1 m of the hole gets a finding.
- Below the thresholds nothing is reported, but the numbers are kept in the diagnostics (how many pairs were checked, how many slivers were below the threshold, the largest one).

## C6 · Name against TERC (medium)

![C6](img/checks/c6.png)

- The name must not be empty.
- The code must exist in TERC.
- The name must be equal to the TERC name, letter by letter, after joining repeated spaces.
- Known exceptions ([`known_exceptions.json`](../voro_teryt_qa/known_exceptions.json)) work only for the exact pair of names. Today there is one: Słupia (Jędrzejowska) in PRG is Słupia in TERC.

## Not checked

The state border (C7, planned), counties and voivodeships themselves, and whether the boundaries agree with the terrain or with legal documents.
