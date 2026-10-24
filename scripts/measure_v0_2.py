"""
Measurement for PREDICTION_v0.2 (P4-P7). Run in the QGIS Python console, with the plugin installed
from this repository (scripts/deploy.sh): Plugins -> Python Console -> Show Editor -> Open Script -> Run.

DATA must hold golden.gpkg, seed_42.gpkg, seed_9.gpkg (from voro-gis-qa, layers gminy, powiaty,
panstwo, known_uncovered) and TERC.csv. Results go to DATA/ref_c7: plugin_<name>.gpkg (findings),
plugin_<name>.html (report), plugin_<name>_log.txt (status, counts, diagnostics, time).
Compare them with voro-gis-qa using scripts/compare_parity.py. QGIS does not respond while it runs.
"""
import os
import time

import processing
from qgis.core import QgsProcessingFeedback, QgsVectorLayer

DATA = r"C:\Users\PC\voro_qgis_data"  # change to your folder
REF = os.path.join(DATA, "ref_c7")
TERC = os.path.join(DATA, "TERC.csv")
RUNS = [
    ("golden", "golden.gpkg", True),
    ("seed_42", "seed_42.gpkg", True),
    ("seed_9", "seed_9.gpkg", True),
    ("seed_42_nostate", "seed_42.gpkg", False),
]


class Log(QgsProcessingFeedback):
    def __init__(self):
        super().__init__()
        self.lines = []

    def pushInfo(self, info):  # noqa: N802
        self.lines.append(info)
        super().pushInfo(info)


def layer(gpkg_path, name):
    lyr = QgsVectorLayer(f"{gpkg_path}|layername={name}", name, "ogr")
    if not lyr.isValid():
        raise RuntimeError(f"Layer {name} not found in {gpkg_path}")
    return lyr


os.makedirs(REF, exist_ok=True)
for name, gpkg, with_state in RUNS:
    path = os.path.join(DATA, gpkg)
    out_gpkg = os.path.join(REF, f"plugin_{name}.gpkg")
    for old in (out_gpkg, out_gpkg.replace(".gpkg", ".html")):
        if os.path.exists(old):
            os.remove(old)
    params = {
        "GMINY": layer(path, "gminy"), "GMINY_TERYT": "teryt", "GMINY_NAME": "name",
        "POWIATY": layer(path, "powiaty"), "POWIATY_TERYT": "teryt",
        "TERC": TERC, "OUTPUT": out_gpkg, "REPORT": out_gpkg.replace(".gpkg", ".html"),
    }
    if with_state:
        params["STATE"] = layer(path, "panstwo")
        params["KNOWN_UNCOVERED"] = layer(path, "known_uncovered")
    print(f"--- {name}: start")
    fb = Log()
    t0 = time.time()
    processing.run("vorotq:boundary_qa", params, feedback=fb)
    dt = time.time() - t0
    with open(os.path.join(REF, f"plugin_{name}_log.txt"), "w", encoding="utf-8") as f:
        f.write(f"{name} | {gpkg} | state+reference: {with_state} | {dt:.1f} s\n")
        f.write("\n".join(fb.lines) + "\n")
    print(f"--- {name}: {dt:.1f} s")
    for line in fb.lines:
        if line.startswith(("Dataset status", "Status zbioru", "  C", "Findings total", "Znaleziska razem")):
            print("   ", line)
print("DONE - results in", REF)
