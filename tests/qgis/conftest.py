"""
Starts QGIS without a window and registers the plugin's Processing provider.
Used by the automatic tests on GitHub (Docker images qgis/qgis) and can be run
anywhere QGIS Python is installed:  python3 -m pytest tests/qgis -v
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from qgis.core import QgsApplication  # noqa: E402

_app = QgsApplication([], False)
_app.initQgis()

for _p in ("/usr/share/qgis/python/plugins", "/usr/lib/qgis/python/plugins"):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.append(_p)

from processing.core.Processing import Processing  # noqa: E402

Processing.initialize()

from voro_teryt_qa.provider import VoroTerytQaProvider  # noqa: E402

_provider = VoroTerytQaProvider()
QgsApplication.processingRegistry().addProvider(_provider)
