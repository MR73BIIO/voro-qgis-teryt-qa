"""
Builds sample_data/ from voro-gis-qa: a small cut of real PRG data, the matching TERC rows,
a copy with one injected error of each type (E1-E8), and the findings that voro-gis-qa
gives on both. The plugin is then tested against these expected findings.

Run with the Python environment of voro-gis-qa (it needs geopandas):
    ~/gis_qa/.venv/bin/python scripts/make_sample_data.py --gisqa ~/gis_qa --counties 1601 1602 1603
"""
import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_terc_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        reader = csv.DictReader(f, dialect=dialect)
        return reader.fieldnames, list(reader), dialect.delimiter


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gisqa", type=Path, required=True, help="folder of voro-gis-qa (with data/golden/golden.gpkg)")
    ap.add_argument("--counties", nargs="+", required=True, help="county codes, 4 digits each")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=Path, default=ROOT / "sample_data")
    a = ap.parse_args()

    sys.path.insert(0, str(a.gisqa / "scripts"))
    import geopandas as gpd
    from checks import judge, load_terc_gminy
    from evaluate import evaluate
    from inject import ALL_TYPES, inject
    from measures import measure

    manifest = json.loads((a.gisqa / "manifest.json").read_text(encoding="utf-8"))
    params = json.loads((a.gisqa / "params.json").read_text(encoding="utf-8"))
    exceptions = json.loads((a.gisqa / "known_exceptions.json").read_text(encoding="utf-8"))
    golden = a.gisqa / "data" / "golden" / "golden.gpkg"
    terc_src = a.gisqa / manifest["terc"]["path"]
    counties = set(a.counties)

    gminy = gpd.read_file(golden, layer="gminy")
    powiaty = gpd.read_file(golden, layer="powiaty")
    gminy = gminy[gminy["teryt"].astype(str).str[:4].isin(counties)][["teryt", "name", "geometry"]]
    powiaty = powiaty[powiaty["teryt"].astype(str).isin(counties)][["teryt", "geometry"]]
    gminy = gminy.sort_values("teryt").reset_index(drop=True)
    powiaty = powiaty.sort_values("teryt").reset_index(drop=True)
    missing = counties - set(powiaty["teryt"].astype(str))
    if missing:
        sys.exit(f"Counties not found in the golden dataset: {sorted(missing)}")
    print(f"Cut: {len(gminy)} municipalities in {len(powiaty)} counties ({' '.join(sorted(counties))})")

    a.out.mkdir(parents=True, exist_ok=True)
    fields, rows, delim = read_terc_rows(terc_src)
    woj = {c[:2] for c in counties}
    keep = [r for r in rows if r["WOJ"].strip() in woj and
            (not r["POW"].strip() or r["WOJ"].strip() + r["POW"].strip() in counties)]
    terc_path = a.out / "terc_sample.csv"
    with open(terc_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter=delim)
        w.writeheader()
        w.writerows(keep)
    terc = load_terc_gminy(terc_path)
    print(f"TERC: {len(keep)} rows, {len(terc)} municipalities")

    def run(g):
        findings, diag = judge(measure(g, powiaty, terc), params, exceptions)
        return [f for f in findings if f["check"] != "C7"], diag

    clean_findings, clean_diag = run(gminy)
    if clean_findings:
        for f in clean_findings[:20]:
            print("  ", f)
        sys.exit("The clean cut is not PASS in voro-gis-qa (see above). Choose other counties.")
    print(f"Clean cut: PASS in voro-gis-qa, {clean_diag.get('c5_overlap_pairs_checked')} pairs checked")

    broken, truth = inject(gminy, powiaty, a.seed, 1, ALL_TYPES, None)
    broken_findings, broken_diag = run(broken)
    record = {"seed": a.seed, "n_injected": len(truth), "injected": truth}
    score = evaluate(record, broken_findings)
    detected = sum(v["detected"] for v in score["per_error"].values())
    false_alarms = sum(m["fp"] for m in score["per_check"].values())
    print(f"Broken copy: {len(truth)} errors injected, {detected} found, {false_alarms} false alarms, "
          f"{len(broken_findings)} findings")

    for name, g in (("sample_clean.gpkg", gminy), ("sample_broken.gpkg", broken)):
        path = a.out / name
        if path.exists():
            path.unlink()
        g.to_file(path, layer="gminy", driver="GPKG")
        powiaty.to_file(path, layer="powiaty", driver="GPKG")

    expected = {
        "made_with": "voro-gis-qa scripts (measures.measure + checks.judge), C7 not included",
        "made_on": date.today().isoformat(),
        "counties": sorted(counties),
        "municipalities": len(gminy),
        "terc_file": manifest["terc"]["path"],
        "seed": a.seed,
        "clean": {"findings": [], "diagnostics": clean_diag},
        "broken": {
            "findings": [{"check": f["check"], "teryt": f["teryt"]} for f in broken_findings],
            "per_check": dict(Counter(f["check"] for f in broken_findings)),
            "diagnostics": broken_diag,
            "injected": [{"error": e["error"], "teryt": e["teryt"], "detail": e["detail"]} for e in truth],
            "detected": detected,
            "false_alarms": false_alarms,
        },
    }
    (a.out / "expected.json").write_text(json.dumps(expected, ensure_ascii=False, indent=1), encoding="utf-8")
    per = expected["broken"]["per_check"]
    table = "\n".join(f"| {c} | {per.get(c, 0)} |" for c in ("C1", "C2", "C3", "C4", "C5", "C6"))
    injected = "\n".join(f"| {e['error']} | {e['teryt']} | {e['detail']} |" for e in expected["broken"]["injected"])
    (a.out / "README.md").write_text(f"""# Sample data / Dane przykładowe

A small cut of real data: {len(gminy)} municipalities in the counties {", ".join(sorted(counties))}.
Mały wycinek prawdziwych danych: {len(gminy)} gmin w powiatach {", ".join(sorted(counties))}.

| File / Plik | What / Co |
|---|---|
| `sample_clean.gpkg` | layers `gminy`, `powiaty` from PRG, unchanged / bez zmian |
| `sample_broken.gpkg` | the same, with one injected error of each type / z jednym wstrzykniętym błędem każdego typu |
| `terc_sample.csv` | TERC rows for these counties / wiersze TERC dla tych powiatów |
| `expected.json` | findings computed by voro-gis-qa / znaleziska policzone przez voro-gis-qa |

## Try it / Wypróbuj

1. Drag `sample_broken.gpkg` into QGIS, add both layers. / Przeciągnij `sample_broken.gpkg` do QGIS, dodaj obie warstwy.
2. Run *VORO TERYT QA → Check boundaries against TERC* with `terc_sample.csv`. / Uruchom algorytm z `terc_sample.csv`.
3. Expected / Oczekiwany wynik: **REJECT, {len(broken_findings)} findings / znalezisk**.
   On / Na `sample_clean.gpkg`: **PASS, 0**.

| Check | Findings on sample_broken |
|---|---|
{table}

Injected errors (seed {a.seed}) / Wstrzyknięte błędy:

| Error | TERYT | Detail |
|---|---|---|
{injected}

voro-gis-qa finds {detected} of {len(truth)} with {false_alarms} false alarms. The automatic tests check that the plugin
gives exactly the same pairs (check, TERYT) as voro-gis-qa on both files, in QGIS 3.40, 3.44 and 4.2.

## Source / Źródło

Boundaries: Państwowy Rejestr Granic (PRG), Główny Urząd Geodezji i Kartografii, geoportal.gov.pl.
TERC: Krajowy Rejestr Urzędowy Podziału Terytorialnego Kraju (TERYT), Główny Urząd Statystyczny.
Made on {date.today().isoformat()} with `scripts/make_sample_data.py`.
""", encoding="utf-8")
    print(f"Per check: {per}")
    print(f"Written to {a.out}")


if __name__ == "__main__":
    main()
