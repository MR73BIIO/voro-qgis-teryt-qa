"""
Parity check: plugin findings vs voro-gis-qa findings, as pairs (check, teryt).

Usage (WSL, no QGIS needed):
    python3 scripts/compare_parity.py --plugin findings.gpkg \
        --gisqa ~/gis_qa/out/findings_XXXX.json --checks C1 C2 C3 C4 C5 C6 \
        [--export-json plugin_findings.json]

--plugin: the Findings layer saved as GeoPackage (.gpkg) or CSV (UTF-8 or cp1250).
--export-json: writes the plugin findings in the voro-gis-qa format, so that
               voro-gis-qa scripts/evaluate.py can score them against truth.json.
Only pairs are compared, not the detail text. Pairs are counted with multiplicity.
"""
import argparse
import csv
import io
import json
import sqlite3
from collections import Counter

FIELDS = ("check", "teryt", "severity", "detail")


def norm(t):
    t = "" if t is None else str(t).strip()
    return None if t in ("", "NULL", "None") else t


def read_csv(path):
    """QGIS on Windows may write CSV in the system encoding (cp1250), not UTF-8."""
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp1250"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"Unknown encoding: {path}")
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    return [{k: r.get(k) for k in FIELDS} for r in rows], f"CSV {enc}"


def read_gpkg(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        tables = [r[0] for r in con.execute(
            "SELECT table_name FROM gpkg_contents WHERE data_type = 'features'")]
        if len(tables) != 1:
            raise ValueError(f"Expected one feature table in {path}, found: {tables}")
        cur = con.execute(f'SELECT "check", "teryt", "severity", "detail" FROM "{tables[0]}"')
        return [dict(zip(FIELDS, r)) for r in cur], f"GPKG table {tables[0]}"
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", required=True)
    ap.add_argument("--gisqa", required=True)
    ap.add_argument("--checks", nargs="+", required=True)
    ap.add_argument("--export-json")
    a = ap.parse_args()
    checks = set(a.checks)

    rows, how = read_gpkg(a.plugin) if a.plugin.lower().endswith(".gpkg") else read_csv(a.plugin)
    for r in rows:
        r["teryt"] = norm(r["teryt"])
    if a.export_json:
        with open(a.export_json, "w", encoding="utf-8") as f:
            json.dump({"source": a.plugin, "findings": rows}, f, ensure_ascii=False, indent=1)

    plugin = Counter((r["check"], r["teryt"]) for r in rows if r["check"] in checks)
    with open(a.gisqa, encoding="utf-8") as f:
        gisqa = Counter((x["check"], norm(x["teryt"])) for x in json.load(f)["findings"] if x["check"] in checks)

    only_plugin = plugin - gisqa
    only_gisqa = gisqa - plugin
    print(f"Checks: {' '.join(sorted(checks))} | plugin file: {how}")
    print(f"plugin: {sum(plugin.values())} findings | voro-gis-qa: {sum(gisqa.values())} findings")
    for c in sorted(checks):
        p = sum(v for (k, _), v in plugin.items() if k == c)
        g = sum(v for (k, _), v in gisqa.items() if k == c)
        print(f"  {c}: plugin {p:>4} | gis_qa {g:>4} | {'OK' if p == g else 'ROZNICA'}")
    for (c, t), n in sorted(only_plugin.items(), key=str)[:40]:
        print(f"  TYLKO WTYCZKA  {c} {t} x{n}")
    for (c, t), n in sorted(only_gisqa.items(), key=str)[:40]:
        print(f"  TYLKO GIS_QA   {c} {t} x{n}")
    print("PARITY: " + ("IDENTICAL" if not only_plugin and not only_gisqa else "DIFFERENT"))
    if a.export_json:
        print(f"Exported for evaluate.py: {a.export_json}")


if __name__ == "__main__":
    main()
