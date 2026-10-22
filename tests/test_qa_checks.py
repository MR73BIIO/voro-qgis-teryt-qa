"""
Logic of the checks (qa_checks), without QGIS.
Run in WSL:  python3 -m pytest tests/test_qa_checks.py -v
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "voro_teryt_qa"))
import qa_checks as q  # noqa: E402

PARAMS = json.loads((ROOT / "voro_teryt_qa" / "params.json").read_text(encoding="utf-8"))
EXCEPTIONS = json.loads((ROOT / "voro_teryt_qa" / "known_exceptions.json").read_text(encoding="utf-8"))
PL_EXTENT = (170000.0, 130000.0, 870000.0, 780000.0)  # roughly Poland in EPSG:2180


def feat(teryt, name="A", ref="A", **kw):
    f = {"teryt": teryt, "name": name, "terc_name": ref, "geom_empty": False, "geom_valid": True,
         "geom_reason": None, "bounds": [500000.0, 500000.0, 501000.0, 501000.0],
         "parent_exists": True, "dist_to_parent_m": 0.0}
    f.update(kw)
    return f


def dataset(*features, **kw):
    m = {"crs": "EPSG:2180", "features": list(features), "n_pairs_checked": 0, "overlaps": [], "gaps": []}
    m.update(kw)
    return m


def pairs(m):
    findings, _ = q.judge(m, PARAMS, EXCEPTIONS, PL_EXTENT)
    return {(f["check"], f["teryt"]) for f in findings}


def test_clean_dataset_has_no_findings():
    findings, diag = q.judge(dataset(feat("0201011"), feat("0201022")), PARAMS, EXCEPTIONS, PL_EXTENT)
    assert findings == []
    assert diag["c6_known_exceptions_applied"] == 0


def test_c1_empty_and_invalid():
    m = dataset(feat("0201011", geom_empty=True, geom_valid=False, bounds=None),
                feat("0201022", geom_valid=False, geom_reason="Self-intersection"))
    assert pairs(m) == {("C1", "0201011"), ("C1", "0201022")}


def test_c2_format_duplicate_type():
    m = dataset(feat("201011"), feat("0201022"), feat("0201022"), feat("0201035"))
    p = pairs(m)
    assert ("C2", "201011") in p
    assert ("C2", "0201022") in p
    assert ("C2", "0201035") in p


def test_c3_missing_county_and_outside():
    m = dataset(feat("0299011", parent_exists=False, dist_to_parent_m=None),
                feat("0201022", dist_to_parent_m=PARAMS["c3_buffer_m"] + 0.5),
                feat("0201032", dist_to_parent_m=PARAMS["c3_buffer_m"]))
    assert pairs(m) == {("C3", "0299011"), ("C3", "0201022")}


def test_c4_wrong_crs_skips_c3_c5():
    m = dataset(feat("0201011", parent_exists=False), crs="EPSG:4326",
                overlaps=[{"a": "0201011", "b": "0201022", "area_m2": 100.0}])
    findings, diag = q.judge(m, PARAMS, EXCEPTIONS, PL_EXTENT)
    assert {(f["check"], f["teryt"]) for f in findings} == {("C4", None)}
    assert "skipped" in diag


def test_c4_missing_crs():
    findings, _ = q.judge(dataset(feat("0201011"), crs=None), PARAMS, EXCEPTIONS, PL_EXTENT)
    assert findings[0]["check"] == "C4" and findings[0]["detail"] == "brak deklaracji CRS"


def test_c4_outside_poland():
    m = dataset(feat("0201011", bounds=[16.0, 51.0, 17.0, 52.0]))
    assert pairs(m) == {("C4", "0201011")}


def test_c5_overlap_threshold():
    tol = PARAMS["c5_overlap_tol_m2"]
    m = dataset(feat("0201011"), feat("0201022"), feat("0201032"),
                overlaps=[{"a": "0201011", "b": "0201022", "area_m2": tol + 0.1},
                          {"a": "0201011", "b": "0201032", "area_m2": tol}], n_pairs_checked=2)
    findings, diag = q.judge(m, PARAMS, EXCEPTIONS, PL_EXTENT)
    assert {(f["check"], f["teryt"]) for f in findings} == {("C5", "0201011"), ("C5", "0201022")}
    assert diag["c5_overlap_pairs_checked"] == 2
    assert diag["c5_overlaps_below_tol"] == 1


def test_c5_gap_reports_every_touching_municipality():
    tol = PARAMS["c5_gap_tol_m2"]
    m = dataset(feat("0201011"), feat("0201022"),
                gaps=[{"area_m2": tol + 5, "touching": ["0201011", "0201022"]},
                      {"area_m2": tol / 2, "touching": ["0201011"]}])
    findings, diag = q.judge(m, PARAMS, EXCEPTIONS, PL_EXTENT)
    assert sorted(f["teryt"] for f in findings) == ["0201011", "0201022"]
    assert diag["c5_gaps_total"] == 2 and diag["c5_gaps_below_tol"] == 1


def test_c6_empty_missing_different():
    m = dataset(feat("0201011", name=""), feat("0201022", ref=None), feat("0201032", name="Gdansk", ref="Gdańsk"))
    assert pairs(m) == {("C6", "0201011"), ("C6", "0201022"), ("C6", "0201032")}


def test_c6_known_exception_only_exact():
    ok = dataset(feat("2602072", name="Słupia (Jędrzejowska)", ref="Słupia"))
    findings, diag = q.judge(ok, PARAMS, EXCEPTIONS, PL_EXTENT)
    assert findings == [] and diag["c6_known_exceptions_applied"] == 1
    broken = dataset(feat("2602072", name="Slupia (Jędrzejowska)", ref="Słupia"))
    assert pairs(broken) == {("C6", "2602072")}


def test_status():
    assert q.status_for(set()) == "PASS"
    assert q.status_for({"srednia"}) == "REVIEW"
    assert q.status_for({"srednia", "krytyczna"}) == "REJECT"


@pytest.mark.parametrize("sep", [";", ","])
def test_load_terc(tmp_path, sep):
    rows = [["WOJ", "POW", "GMI", "RODZ", "NAZWA", "NAZWA_DOD", "STAN_NA"],
            ["02", "", "", "", "DOLNOŚLĄSKIE", "województwo", "2026-01-01"],
            ["02", "01", "", "", "bolesławiecki", "powiat", "2026-01-01"],
            ["02", "01", "01", "1", "Bolesławiec", "gmina miejska", "2026-01-01"],
            ["02", "01", "02", "2", "Bolesławiec", "gmina wiejska", "2026-01-01"],
            ["02", "01", "03", "4", "Nowogrodziec", "miasto", "2026-01-01"]]
    path = tmp_path / "terc.csv"
    path.write_text("\n".join(sep.join(r) for r in rows), encoding="utf-8-sig")
    assert q.load_terc_gminy(path) == {"0201011": "Bolesławiec", "0201022": "Bolesławiec"}
