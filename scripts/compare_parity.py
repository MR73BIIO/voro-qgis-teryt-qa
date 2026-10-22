"""
Parity check: plugin findings vs voro-gis-qa findings, as pairs (check, teryt).

Usage (WSL, no QGIS needed):
    python3 scripts/compare_parity.py --plugin findings_plugin.csv \
        --gisqa ~/gis_qa/out/findings_XXXX.json --checks C1 C2 C4 C6

The plugin CSV is the Findings layer saved as CSV (fields check, teryt, severity, detail).
Only pairs are compared, not the detail text.
"""
import argparse
import csv
import io
import json
from collections import Counter


def norm(t):
    t = "" if t is None else str(t).strip()
    return None if t in ("", "NULL", "None") else t


def read_text(path):
    """QGIS on Windows may write CSV in the system encoding (cp1250), not UTF-8."""
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "cp1250"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unknown encoding: {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", required=True)
    ap.add_argument("--gisqa", required=True)
    ap.add_argument("--checks", nargs="+", required=True)
    a = ap.parse_args()
    checks = set(a.checks)

    text, enc = read_text(a.plugin)
    rows = csv.DictReader(io.StringIO(text, newline=""))
    plugin = Counter((r["check"], norm(r["teryt"])) for r in rows if r["check"] in checks)
    with open(a.gisqa, encoding="utf-8") as f:
        gisqa = Counter((x["check"], norm(x["teryt"])) for x in json.load(f)["findings"] if x["check"] in checks)

    only_plugin = plugin - gisqa
    only_gisqa = gisqa - plugin
    print(f"Checks: {' '.join(sorted(checks))} | plugin CSV encoding: {enc}")
    print(f"plugin: {sum(plugin.values())} findings | voro-gis-qa: {sum(gisqa.values())} findings")
    for c in sorted(checks):
        p = sum(v for (k, _), v in plugin.items() if k == c)
        g = sum(v for (k, _), v in gisqa.items() if k == c)
        print(f"  {c}: plugin {p:>4} | gis_qa {g:>4} | {'OK' if p == g else 'ROZNICA'}")
    for (c, t), n in sorted(only_plugin.items(), key=str):
        print(f"  TYLKO WTYCZKA  {c} {t} x{n}")
    for (c, t), n in sorted(only_gisqa.items(), key=str):
        print(f"  TYLKO GIS_QA   {c} {t} x{n}")
    print("PARITY: " + ("IDENTICAL" if not only_plugin and not only_gisqa else "DIFFERENT"))


if __name__ == "__main__":
    main()
