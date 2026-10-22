# voro-qgis-teryt-qa

QGIS plugin for quality checks of Polish administrative boundaries (PRG) against the official TERC register.

The checks come from [voro-gis-qa](https://github.com/MR73BIIO/voro-gis-qa), where they were built and measured in Python. This repository moves them into QGIS as a Processing algorithm: *VORO TERYT QA → Check boundaries against TERC*.

## Status

Version 0.0.2, tested in QGIS 3.44.15 on Windows.

Checks in the plugin now:

| Check | What it looks at |
|---|---|
| C1 | empty or invalid geometry |
| C2 | TERYT format, duplicates, municipality type 1/2/3 |
| C4 | declared CRS, geometry inside the extent of Poland |
| C6 | name present and equal to TERC |

Next: C3 (municipality inside its own county) and C5 (overlaps and gaps).

Measured so far, against the prediction in `PREDICTION.md`:

- Golden dataset, 2479 municipalities: 0 findings, status PASS, the one known C6 exception applied once.
- `seed_42` from voro-gis-qa (160 injected errors): the plugin and voro-gis-qa give the same 139 pairs (check, TERYT) for C1, C2, C4 and C6. C1 20, C2 20, C4 20, C6 79. Compared with `scripts/compare_parity.py`.

One thing learned on the way: Processing stops on invalid geometries by default. A QA tool has to read them, so the plugin switches that filter off for its own read of the municipalities layer.

## License

GPL-2.0-or-later, as required for plugins in the official QGIS repository.

---

Marcin Ruszczak · MR73BIIO · Polish, German, Russian, English
