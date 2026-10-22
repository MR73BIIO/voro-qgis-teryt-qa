"""
MEASUREMENTS of the municipality layer in PyQGIS - same schema as voro-gis-qa measures.measure().
No thresholds and no judgement here; that is done in qa_checks.

Stage 2: per-feature facts (geometry, TERYT, name, TERC name, bounding box) and the CRS.
Stage 3 adds: parent county, overlaps, gaps.
"""
from qgis.core import Qgis, QgsFeatureRequest


def _text(v):
    """Attribute -> str. NULL from QGIS 3 (QVariant) and None from QGIS 4 both give ''."""
    if v is None or (hasattr(v, "isNull") and v.isNull()):
        return ""
    return str(v)


def _invalid_reason(geom):
    errors = geom.validateGeometry(Qgis.GeometryValidationEngine.Geos)
    if errors:
        return errors[0].what()
    return "niepoprawna geometria"


def measure(source, teryt_field, name_field, terc, feedback=None):
    """Facts about the municipalities. Returns (m, geometries) where geometries[row] = QgsGeometry."""
    features, geometries = [], []
    total = source.featureCount() or 1
    # A QA tool must read invalid geometries to report them (C1), so the Processing
    # "invalid features filtering" is switched off here, only for this read.
    features_iter = source.getFeatures(QgsFeatureRequest(),
                                       Qgis.ProcessingFeatureSourceFlag.SkipGeometryValidityChecks)
    for i, feat in enumerate(features_iter):
        if feedback is not None:
            if feedback.isCanceled():
                break
            feedback.setProgress(100.0 * i / total)
        t = _text(feat[teryt_field])
        name = " ".join(_text(feat[name_field]).split())
        geom = feat.geometry()
        empty = geom is None or geom.isNull() or geom.isEmpty()
        valid = (not empty) and geom.isGeosValid()
        bb = None if empty else geom.boundingBox()
        features.append({
            "row": i,
            "teryt": t,
            "name": name,
            "geom_empty": bool(empty),
            "geom_valid": bool(valid),
            "geom_reason": None if valid or empty else _invalid_reason(geom),
            "bounds": None if empty else [bb.xMinimum(), bb.yMinimum(), bb.xMaximum(), bb.yMaximum()],
            "terc_name": terc.get(t),
        })
        geometries.append(geom)

    crs = source.sourceCrs()
    m = {
        "crs": crs.authid() if crs.isValid() and crs.authid() else None,
        "n_features": len(features),
        "features": features,
    }
    return m, geometries
