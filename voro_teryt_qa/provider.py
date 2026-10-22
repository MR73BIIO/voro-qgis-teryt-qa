"""Processing provider: the group 'VORO TERYT QA' in the Processing Toolbox."""
from qgis.core import QgsProcessingProvider

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
