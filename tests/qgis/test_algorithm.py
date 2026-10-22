"""
The whole algorithm inside QGIS, on a small synthetic dataset:
2 counties x 4 municipalities, squares of 1 km in EPSG:2180 (as in voro-gis-qa tests).
Each test breaks one thing and checks that the expected check reports it.
"""
from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsRectangle,
    QgsVectorLayer,
)
import processing

X0, Y0 = 500000.0, 500000.0
COUNTIES = ["0401", "0402"]
NAMES = ["Łódź", "Kraków", "Gdańsk", "Żary", "Ełk", "Śrem", "Nysa", "Oława"]
ALG = "vorotq:boundary_qa"


def clean_data():
    """Returns (municipalities, counties) as lists of (teryt, name, QgsGeometry)."""
    gminy, powiaty, k = [], [], 0
    for pi, pc in enumerate(COUNTIES):
        px = X0 + pi * 2000
        powiaty.append((pc, None, QgsGeometry.fromRect(QgsRectangle(px, Y0, px + 2000, Y0 + 2000))))
        for i in range(2):
            for j in range(2):
                rect = QgsRectangle(px + i * 1000, Y0 + j * 1000, px + (i + 1) * 1000, Y0 + (j + 1) * 1000)
                gminy.append([f"{pc}{k + 1:02d}1", NAMES[k], QgsGeometry.fromRect(rect)])
                k += 1
    return gminy, powiaty


def layer(rows, name, crs="EPSG:2180"):
    lyr = QgsVectorLayer(f"Polygon?crs={crs}&field=teryt:string(10)&field=name:string(80)", name, "memory")
    feats = []
    for teryt, nm, geom in rows:
        f = QgsFeature(lyr.fields())
        f.setAttributes([teryt, nm])
        f.setGeometry(geom)
        feats.append(f)
    assert lyr.dataProvider().addFeatures(feats)
    return lyr


def terc_file(tmp_path, gminy, extra=()):
    lines = ["WOJ;POW;GMI;RODZ;NAZWA;NAZWA_DOD;STAN_NA"]
    for teryt, name in [(t, n) for t, n, _ in gminy] + list(extra):
        lines.append(f"{teryt[:2]};{teryt[2:4]};{teryt[4:6]};{teryt[6]};{name};gmina;2026-01-01")
    path = tmp_path / "terc.csv"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def run(tmp_path, gminy, powiaty, terc=None, gminy_crs="EPSG:2180"):
    terc = terc or terc_file(tmp_path, gminy)
    out = tmp_path / "findings.gpkg"
    res = processing.run(ALG, {
        "GMINY": layer(gminy, "gminy", gminy_crs), "GMINY_TERYT": "teryt", "GMINY_NAME": "name",
        "POWIATY": layer(powiaty, "powiaty"), "POWIATY_TERYT": "teryt",
        "TERC": str(terc), "OUTPUT": str(out)})
    result = QgsVectorLayer(res["OUTPUT"], "findings", "ogr")
    assert result.isValid()
    rows = []
    for f in result.getFeatures():
        t = f["teryt"]
        t = None if t is None or (hasattr(t, "isNull") and t.isNull()) or t == "" else str(t)
        rows.append((f["check"], t, f["detail"]))
    return rows


def checks_of(rows, teryt):
    return {c for c, t, _ in rows if t == teryt}


def test_algorithm_is_registered():
    from qgis.core import QgsApplication
    assert QgsApplication.processingRegistry().algorithmById(ALG) is not None


def test_clean_has_no_findings(tmp_path):
    gminy, powiaty = clean_data()
    assert run(tmp_path, gminy, powiaty) == []


def test_c1_invalid_geometry_does_not_stop_the_algorithm(tmp_path):
    """Regression: Processing stops on invalid geometries unless the plugin switches that off."""
    gminy, powiaty = clean_data()
    x, y = X0 + 1000, Y0 + 1000
    gminy[3][2] = QgsGeometry.fromWkt(f"POLYGON(({x} {y},{x + 1000} {y + 1000},{x + 1000} {y},{x} {y + 1000},{x} {y}))")
    rows = run(tmp_path, gminy, powiaty)
    assert "C1" in checks_of(rows, gminy[3][0])


def test_c2_duplicate_teryt(tmp_path):
    gminy, powiaty = clean_data()
    terc = terc_file(tmp_path, gminy)
    gminy[0][0] = gminy[1][0]
    assert "C2" in checks_of(run(tmp_path, gminy, powiaty, terc), gminy[1][0])


def test_c3_county_does_not_exist(tmp_path):
    gminy, powiaty = clean_data()
    gminy[6][0] = "0409071"
    assert "C3" in checks_of(run(tmp_path, gminy, powiaty), "0409071")


def test_c3_municipality_in_the_wrong_county(tmp_path):
    gminy, powiaty = clean_data()
    gminy[0][0] = "0402091"  # geometry in county 0401, code says 0402
    assert "C3" in checks_of(run(tmp_path, gminy, powiaty), "0402091")


def test_c4_wrong_crs(tmp_path):
    gminy, powiaty = clean_data()
    rows = run(tmp_path, gminy, powiaty, gminy_crs="EPSG:4326")
    assert ("C4", None) in {(c, t) for c, t, _ in rows}


def test_c4_outside_poland(tmp_path):
    gminy, powiaty = clean_data()
    gminy[7][2] = QgsGeometry.fromRect(QgsRectangle(5000000, 5000000, 5001000, 5001000))
    assert "C4" in checks_of(run(tmp_path, gminy, powiaty), gminy[7][0])


def test_c5_shift_gives_overlap(tmp_path):
    gminy, powiaty = clean_data()
    g = QgsGeometry(gminy[4][2])
    g.translate(50, 0)
    gminy[4][2] = g
    rows = run(tmp_path, gminy, powiaty)
    assert any(c == "C5" and t == gminy[4][0] and "nakladanie" in d for c, t, d in rows)


def test_c5_gap_between_two_municipalities(tmp_path):
    gminy, powiaty = clean_data()
    cut = QgsGeometry.fromRect(QgsRectangle(X0 + 990, Y0 + 400, X0 + 1000, Y0 + 600))
    gminy[0][2] = gminy[0][2].difference(cut)
    rows = run(tmp_path, gminy, powiaty)
    assert any(c == "C5" and "szczelina" in d for c, t, d in rows)


def test_c6_lost_diacritics(tmp_path):
    gminy, powiaty = clean_data()
    terc = terc_file(tmp_path, gminy)
    gminy[2][1] = "Gdansk"
    assert "C6" in checks_of(run(tmp_path, gminy, powiaty, terc), gminy[2][0])


def test_c6_shipped_exception_slupia(tmp_path):
    """The exception from known_exceptions.json works only for the exact pair of names."""
    powiaty = [("2602", None, QgsGeometry.fromRect(QgsRectangle(X0, Y0, X0 + 2000, Y0 + 2000)))]
    geom = QgsGeometry.fromRect(QgsRectangle(X0, Y0, X0 + 1000, Y0 + 1000))
    terc = tmp_path / "terc_slupia.csv"
    terc.write_text("WOJ;POW;GMI;RODZ;NAZWA;NAZWA_DOD;STAN_NA\n26;02;07;2;Słupia;gmina wiejska;2026-01-01",
                    encoding="utf-8")
    assert run(tmp_path, [["2602072", "Słupia (Jędrzejowska)", geom]], powiaty, terc) == []
    rows = run(tmp_path, [["2602072", "Slupia (Jędrzejowska)", geom]], powiaty, terc)
    assert checks_of(rows, "2602072") == {"C6"}
