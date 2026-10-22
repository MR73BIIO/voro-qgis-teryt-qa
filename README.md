**English** | [Polski](README.pl.md)

# VORO TERYT QA

[![tests](https://github.com/MR73BIIO/voro-qgis-teryt-qa/actions/workflows/tests.yml/badge.svg)](https://github.com/MR73BIIO/voro-qgis-teryt-qa/actions/workflows/tests.yml)
![QGIS](https://img.shields.io/badge/QGIS-3.40%20%7C%203.44%20%7C%204.2-589632)
![License](https://img.shields.io/badge/license-GPL--2.0--or--later-blue)

**QGIS plugin that checks Polish municipality boundaries (PRG) against the official TERC register, and shows every problem on the map.**

![Findings on the test dataset seed_42](docs/img/map_findings.png)

Boundary data is often accepted after a look at the map. This plugin gives a check that can be repeated: the same rules, the same thresholds, the same result on any computer. It was built from [voro-gis-qa](https://github.com/MR73BIIO/voro-gis-qa), where the rules were first measured in Python, and it gives the same findings.

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

How each check works, with pictures: [`docs/checks.md`](docs/checks.md).

## What you get

A Processing algorithm, in Polish or English depending on the QGIS language. On the clean PRG layer it returns PASS:

![The algorithm in QGIS: golden dataset, status PASS](docs/img/dialog_pass.png)

A layer of findings, one row per problem, with the geometry of the municipality (the map above). And, if you want it, an HTML report in Polish that can be printed or sent:

![HTML report](docs/img/report.png)

## Install

Download `voro_teryt_qa-0.1.0.zip` from [Releases](https://github.com/MR73BIIO/voro-qgis-teryt-qa/releases). In QGIS: *Plugins → Manage and Install Plugins → Install from ZIP*.

![The plugin in the QGIS plugin manager](docs/img/plugin_manager.png)

Requirements: QGIS 3.40 or newer, including QGIS 4. No extra Python packages.

## Use

1. Load the municipalities and counties layers (for example from PRG) in EPSG:2180.
2. Run *VORO TERYT QA → Check boundaries against TERC* from the Processing Toolbox.
3. Choose the layers, the TERYT and name fields, and the TERC file (CSV from GUS).
4. Optionally choose a file for the HTML report.
5. Do not switch on "iterate over this layer". Overlaps, gaps and duplicates exist only between municipalities.

On the full PRG layer (2479 municipalities) a run takes about one minute.

## How it was tested

The prediction for version 0.1 was written in [`PREDICTION.md`](PREDICTION.md) before any plugin code. All three parts hold:

| Prediction | Result |
|---|---|
| P1: golden dataset (2479 municipalities) gives no findings | 0 findings, PASS. 7075 pairs of municipalities checked, the same number as in voro-gis-qa |
| P2: all injected errors found, no false alarms | `seed_42`, 160 errors (20 of each type): 160 of 160 found, 0 false alarms |
| P3: the same answers as voro-gis-qa | 2335 of 2335 pairs (check, TERYT) identical. One difference in diagnostics, without effect: [`docs/differences.md`](docs/differences.md) |

Automatic checks run on every push: code check (ruff), 23 tests of the logic, the report and the translations, and 13 tests of the whole plugin inside QGIS 3.40, 3.44 and 4.2 on Linux. Manual runs: QGIS 3.44.15 on Windows.

## What it does not check

The state border (C7, planned), counties and voivodeships themselves, and whether the boundaries agree with the terrain or with legal documents. The check compares the data with itself and with the TERC register.

## License

GPL-2.0-or-later. Citation data: [`CITATION.cff`](CITATION.cff). Changes: [`CHANGELOG.md`](CHANGELOG.md).

---

Marcin Ruszczak · MR73BIIO · Polish, German, Russian, English
