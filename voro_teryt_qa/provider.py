"""Processing provider: the group 'VORO TERYT QA' in the Processing Toolbox."""
import os

from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .algorithm import BoundaryQaAlgorithm


class VoroTerytQaProvider(QgsProcessingProvider):
    def loadAlgorithms(self):  # noqa: N802 (QGIS name)
        self.addAlgorithm(BoundaryQaAlgorithm())

    def id(self):
        return "vorotq"

    def name(self):
        return "VORO TERYT QA"

    def longName(self):  # noqa: N802 (QGIS name)
        return self.name()

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))
