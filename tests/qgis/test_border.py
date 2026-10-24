"""
C7 (state border) inside QGIS, on the synthetic world of voro-gis-qa tests/test_border.py:
10 x 10 municipalities of 1 km, 4 counties, and a 'sea' strip in the north of the state layer.
measure() and judge() are called directly, so the exceptions are set per test, as in voro-gis-qa.
The last test runs the whole algorithm with the new optional input 'State border'.
"""
import json
from pathlib import Path

import processing
from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProcessingContext,
    QgsProcessingFeatureSource,
    QgsRectangle,
    QgsVectorLayer,
)

from voro_teryt_qa import qa_checks
from voro_teryt_qa.qa_measures import measure

ROOT = Path(__file__).resolve().parents[2]
PARAMS = json.loads((ROOT / "voro_teryt_qa" / "params.json").read_text(encoding="utf-8"))
PL_EXTENT = (170000.0, 130000.0, 870000.0, 780000.0)  # roughly Poland in EPSG:2180
X0 = Y0 = 500000.0
_KEEP = []  # layers and contexts must live as long as the sources made from them


def rect(x0, y0, x1, y1):
    return QgsGeometry.fromRect(QgsRectangle(x0, y0, x1, y1))


def half_disc_cut(x, y, r=50.0):
    return QgsGeometry.fromPointXY(QgsPointXY(x, y)).buffer(r, 16)


def memory_layer(rows, name):
    lyr = QgsVectorLayer("Polygon?crs=EPSG:2180&field=teryt:string(10)&field=name:string(80)", name, "memory")
    feats = []
    for teryt, nm, geom in rows:
        f = QgsFeature(lyr.fields())
        f.setAttributes([teryt, nm])
        f.setGeometry(geom)
        feats.append(f)
    assert lyr.dataProvider().addFeatures(feats)
    return lyr


def source(rows, name):
    lyr = memory_layer(rows, name)
    ctx = QgsProcessingContext()
    _KEEP.extend([lyr, ctx])
    return QgsProcessingFeatureSource(lyr, ctx)


def world():
    gminy, powiaty = [], []
    for pi in range(2):
        for pj in range(2):
            pc = f"04{pi * 2 + pj + 1:02d}"
            powiaty.append((pc, None, rect(X0 + pi * 5000, Y0 + pj * 5000,
                                           X0 + (pi + 1) * 5000, Y0 + (pj + 1) * 5000)))
            k = 0
            for i in range(5):
                for j in range(5):
                    k += 1
                    x, y = X0 + pi * 5000 + i * 1000, Y0 + pj * 5000 + j * 1000
                    gminy.append([f"{pc}{k:02d}2", f"Łąka {pc}-{k}", rect(x, y, x + 1000, y + 1000)])
    sea = rect(X0, Y0 + 10000, X0 + 10000, Y0 + 12000)
    state = QgsGeometry.unaryUnion([g for _, _, g in gminy] + [sea])
    exc = [{"check": "C7", "kind": "uncovered", "area_m2": sea.area(), "tolerance_m2": 1.0}]
    return gminy, powiaty, state, sea, exc


def check(gminy, powiaty, state=None, sea=None, exc=()):
    terc = {t: n for t, n, _ in gminy}
    m, _ = measure(source(gminy, "gminy"), "teryt", "name", terc, source(powiaty, "powiaty"), "teryt",
                   state=None if state is None else [state], reference=None if sea is None else [sea])
    return qa_checks.judge(m, PARAMS, list(exc), PL_EXTENT)


def test_golden_with_sea_is_clean():
    gminy, powiaty, state, sea, exc = world()
    findings, diag = check(gminy, powiaty, state, sea, exc)
    assert findings == []
    assert diag["c7_known_exceptions_applied"] == 1


def test_sea_without_exception_is_reported():
    gminy, powiaty, state, sea, _ = world()
    findings, _ = check(gminy, powiaty, state, sea, [])
    assert any(f["check"] == "C7" for f in findings)


def test_no_state_layer_skips_c7():
    gminy, powiaty, _, _, exc = world()
    findings, diag = check(gminy, powiaty, exc=exc)
    assert findings == [] and "c7" in diag


def test_gaps_cut_at_the_state_border_are_found():
    """E9 as in voro-gis-qa: a half disc cut where a municipality meets the state border
    (west, south and east edge). Only the cut municipalities get C7, nothing else is reported."""
    gminy, powiaty, state, sea, exc = world()
    cuts = {0: (X0, Y0 + 500), 50: (X0 + 5500, Y0), 70: (X0 + 10000, Y0 + 500)}
    for i, (x, y) in cuts.items():
        gminy[i][2] = gminy[i][2].difference(half_disc_cut(x, y))
    findings, diag = check(gminy, powiaty, state, sea, exc)
    assert {(f["check"], f["teryt"]) for f in findings} == {("C7", gminy[i][0]) for i in cuts}
    assert diag["c7_known_exceptions_applied"] == 1


def test_coastal_gap_stays_local():
    """A hole at the coast must not 'infect' all coastal municipalities (note_1.6)."""
    gminy, powiaty, state, sea, exc = world()
    coastal = [i for i, (_, _, g) in enumerate(gminy) if g.boundingBox().yMaximum() == Y0 + 10000]
    i = coastal[3]
    bb = gminy[i][2].boundingBox()
    xm, y1 = (bb.xMinimum() + bb.xMaximum()) / 2, bb.yMaximum()
    gminy[i][2] = gminy[i][2].difference(rect(xm - 50, y1 - 50, xm + 50, y1))
    findings, diag = check(gminy, powiaty, state, sea, exc)
    c7 = {f["teryt"] for f in findings if f["check"] == "C7"}
    assert gminy[i][0] in c7
    assert len(c7) <= 3
    assert diag["c7_known_exceptions_applied"] == 1


def run_alg(params):
    res = processing.run("vorotq:boundary_qa", params)
    out = set()
    for f in QgsVectorLayer(res["OUTPUT"], "f", "ogr").getFeatures():
        t = f["teryt"]
        t = None if t is None or (hasattr(t, "isNull") and t.isNull()) or t == "" else str(t)
        out.add((f["check"], t))
    return out


def test_algorithm_uses_the_optional_state_layer(tmp_path):
    """Without the state layer the result is as in v0.1.1; with it the cut at the border is C7.
    No sea here, so the shipped known exceptions do not take part."""
    gminy, powiaty, _, _, _ = world()
    state = QgsGeometry.unaryUnion([g for _, _, g in gminy])
    gminy[0][2] = gminy[0][2].difference(half_disc_cut(X0, Y0 + 500))
    terc = tmp_path / "terc.csv"
    lines = ["WOJ;POW;GMI;RODZ;NAZWA;NAZWA_DOD;STAN_NA"]
    lines += [f"{t[:2]};{t[2:4]};{t[4:6]};{t[6]};{n};gmina;2026-01-01" for t, n, _ in gminy]
    terc.write_text("\n".join(lines), encoding="utf-8")
    params = {"GMINY": memory_layer(gminy, "gminy"), "GMINY_TERYT": "teryt", "GMINY_NAME": "name",
              "POWIATY": memory_layer(powiaty, "powiaty"), "POWIATY_TERYT": "teryt",
              "TERC": str(terc), "OUTPUT": str(tmp_path / "without_state.gpkg")}
    assert run_alg(params) == set()
    params.update(STATE=memory_layer([("PL", "Polska", state)], "panstwo"),
                  OUTPUT=str(tmp_path / "with_state.gpkg"))
    assert run_alg(params) == {("C7", gminy[0][0])}
