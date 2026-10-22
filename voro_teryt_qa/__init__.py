"""VORO TERYT QA - QGIS plugin entry point."""


def classFactory(iface):  # noqa: N802 (QGIS name)
    from .plugin import VoroTerytQaPlugin
    return VoroTerytQaPlugin(iface)
