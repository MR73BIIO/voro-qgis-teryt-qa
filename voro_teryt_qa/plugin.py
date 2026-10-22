"""Plugin class: registers the Processing provider and removes it on unload."""
from qgis.core import QgsApplication

from .provider import VoroTerytQaProvider


class VoroTerytQaPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initProcessing(self):  # noqa: N802 (QGIS name)
        self.provider = VoroTerytQaProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):  # noqa: N802 (QGIS name)
        self.initProcessing()

    def unload(self):
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
