"""
The plugin on real PRG data from sample_data/ (a cut made by scripts/make_sample_data.py).
The expected findings were computed by voro-gis-qa, not by the plugin.
"""
import json
from collections import Counter
from pathlib import Path

import processing
import pytest
from qgis.core import QgsVectorLayer

SAMPLE = Path(__file__).resolve().parents[2] / "sample_data"
ALG = "vorotq:boundary_qa"
pytestmark = pytest.mark.skipif(not (SAMPLE / "expected.json").exists(), reason="no sample_data")


def run(tmp_path, gpkg):
    gminy = QgsVectorLayer(f"{SAMPLE / gpkg}|layername=gminy", "gminy", "ogr")
    powiaty = QgsVectorLayer(f"{SAMPLE / gpkg}|layername=powiaty", "powiaty", "ogr")
    assert gminy.isValid() and powiaty.isValid()
    out = tmp_path / f"findings_{gpkg}"
    res = processing.run(ALG, {
        "GMINY": gminy, "GMINY_TERYT": "teryt", "GMINY_NAME": "name",
        "POWIATY": powiaty, "POWIATY_TERYT": "teryt",
        "TERC": str(SAMPLE / "terc_sample.csv"), "OUTPUT": str(out)})
    pairs = Counter()
    for f in QgsVectorLayer(res["OUTPUT"], "f", "ogr").getFeatures():
        t = f["teryt"]
        t = None if t is None or (hasattr(t, "isNull") and t.isNull()) or t == "" else str(t)
        pairs[(f["check"], t)] += 1
    return pairs


def expected():
    return json.loads((SAMPLE / "expected.json").read_text(encoding="utf-8"))


def test_clean_sample_is_pass(tmp_path):
    assert run(tmp_path, "sample_clean.gpkg") == Counter()


def test_broken_sample_matches_voro_gis_qa(tmp_path):
    want = Counter((f["check"], f["teryt"]) for f in expected()["broken"]["findings"])
    got = run(tmp_path, "sample_broken.gpkg")
    assert got == want, f"only plugin: {got - want}, only voro-gis-qa: {want - got}"


def test_every_injected_error_is_reported(tmp_path):
    got = run(tmp_path, "sample_broken.gpkg")
    reported = {t for _, t in got}
    for e in expected()["broken"]["injected"]:
        assert e["teryt"] in reported, e
