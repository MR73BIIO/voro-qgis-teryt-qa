**English** | [Polski](README.pl.md)

# voro-qgis-teryt-qa

QGIS plugin for quality checks of Polish municipality boundaries (PRG) against the official TERC register.

It adds one Processing algorithm: **VORO TERYT QA → Check boundaries against TERC**. You give it the municipalities layer, the counties layer and the TERC file. It returns a layer of findings, one row per problem, with the geometry of the municipality, so the errors can be seen on the map. Optionally it writes an HTML report.

The checks were first built and measured in Python in [voro-gis-qa](https://github.com/MR73BIIO/voro-gis-qa). This plugin moves them into QGIS without changing the rules or the thresholds.

## What it checks

| Check | What it looks at | Severity |
|---|---|---|
| C1 | empty or invalid geometry | critical |
| C2 | TERYT format, duplicates, municipality type 1/2/3 | critical |
| C3 | municipality inside its own county | critical |
| C4 | declared CRS, geometry inside the extent of Poland | critical |
| C5 | overlaps and gaps between municipalities | high |
| C6 | name present and equal to TERC | medium |

Status of the whole dataset: **PASS** (no findings), **REVIEW** (findings, none critical), **REJECT** (at least one critical finding).

Not checked in this version: the state border (C7), counties and voivodeships themselves, the boundaries against the terrain or legal documents.

## Install

Until the plugin is in the official QGIS repository: download the ZIP from the Releases page, then in QGIS *Plugins → Manage and Install Plugins → Install from ZIP*.

Requirements: QGIS 3.40 or newer, including QGIS 4. No extra Python packages.

## Use

1. Load the municipalities and counties layers (for example from PRG) in EPSG:2180.
2. Open the Processing Toolbox and run *VORO TERYT QA → Check boundaries against TERC*.
3. Choose the layers, the TERYT and name fields, and the TERC file (CSV from GUS).
4. Optionally choose a file for the HTML report.
5. Do not switch on "iterate over this layer". Overlaps, gaps and duplicates exist only between municipalities.

On the full PRG layer (2479 municipalities) a run takes about one minute.

The interface is in Polish when QGIS runs in Polish, and in English otherwise. The HTML report is in Polish.

## How it was tested

The prediction for version 0.1 was written down in `PREDICTION.md` before any plugin code. Results:

- **Golden dataset** (2479 municipalities, 380 counties): 0 findings, status PASS. 7075 pairs of municipalities checked for overlaps, the same number as in voro-gis-qa.
- **`seed_42`** from voro-gis-qa (160 injected errors, 20 of each type): 160 of 160 found with the expected check, 0 false alarms.
- **Same answers as voro-gis-qa:** 2335 pairs (check, TERYT) on `seed_42`, identical. One difference in the diagnostics, without effect on findings, is described in `docs/differences.md`.

Automatic tests run on every push (GitHub Actions): 23 tests of the logic, the report and the translations, without QGIS, and 13 tests of the whole plugin inside QGIS 3.40, 3.44 and 4.2 on Linux. Manual runs: QGIS 3.44.15 on Windows.

## License

GPL-2.0-or-later.

---

Marcin Ruszczak · MR73BIIO · Polish, German, Russian, English
