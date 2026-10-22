"""
MEASUREMENTS in PyQGIS - same schema as voro-gis-qa measures.measure() (544fbec).
No thresholds and no judgement here; that is done in qa_checks.

Per municipality: geometry, TERYT, name, TERC name, bounding box, parent county, distance
of a point on the surface to the parent county.
For the whole layer: overlaps between municipalities and gaps (holes in the union).
The state border (C7) is not measured in v0.1.
"""
from qgis.core import Qgis, QgsFeatureRequest, QgsGeometry, QgsSpatialIndex

from .i18n import tr

BUFFER_SEGMENTS = 16  # shapely default quad_segs, so the 1 m buffer around a gap is the same shape


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


def _read_all(source):
    """A QA tool must read invalid geometries to report them (C1), so the Processing
    'invalid features filtering' is switched off, only for this read."""
    return source.getFeatures(QgsFeatureRequest(),
                              Qgis.ProcessingFeatureSourceFlag.SkipGeometryValidityChecks)


def _empty(geom):
    return geom is None or geom.isNull() or geom.isEmpty()


def _rings_of_holes(geom):
    """Interior rings of every polygon part, each as a polygon geometry."""
    parts = geom.asMultiPolygon() if geom.isMultipart() else [geom.asPolygon()]
    for poly in parts:
        for ring in poly[1:]:
            yield QgsGeometry.fromPolygonXY([ring])


def measure(source, teryt_field, name_field, terc, powiaty, powiaty_teryt_field, feedback=None):
    """Facts about the municipalities. Returns (m, geometries) where geometries[row] = QgsGeometry."""
    def step(text):
        if feedback is not None:
            feedback.setProgressText(tr(text))

    def canceled():
        return feedback is not None and feedback.isCanceled()

    step("Reading counties")
    pow_geom = {}
    for pf in _read_all(powiaty):
        pow_geom[_text(pf[powiaty_teryt_field])] = pf.geometry()

    step("Measuring municipalities")
    features, geometries = [], []
    total = source.featureCount() or 1
    for i, feat in enumerate(_read_all(source)):
        if canceled():
            return None, None
        if feedback is not None:
            feedback.setProgress(40.0 * i / total)
        t = _text(feat[teryt_field])
        name = " ".join(_text(feat[name_field]).split())
        geom = feat.geometry()
        empty = _empty(geom)
        valid = (not empty) and geom.isGeosValid()
        bb = None if empty else geom.boundingBox()
        parent = t[:4]
        dist = None
        if valid and parent in pow_geom:
            dist = float(pow_geom[parent].distance(geom.pointOnSurface()))
        features.append({
            "row": i,
            "teryt": t,
            "name": name,
            "geom_empty": bool(empty),
            "geom_valid": bool(valid),
            "geom_reason": None if valid or empty else _invalid_reason(geom),
            "bounds": None if empty else [bb.xMinimum(), bb.yMinimum(), bb.xMaximum(), bb.yMaximum()],
            "parent_exists": parent in pow_geom,
            "dist_to_parent_m": dist,
            "terc_name": terc.get(t),
        })
        geometries.append(geom)

    # only valid geometries take part in overlaps and gaps, as in voro-gis-qa
    ok = [f["row"] for f in features if f["geom_valid"]]
    geoms = [geometries[r] for r in ok]
    t_ok = [features[r]["teryt"] for r in ok]
    index = QgsSpatialIndex()
    for k, g in enumerate(geoms):
        index.addFeature(k, g.boundingBox())

    step("Overlaps between municipalities")
    overlaps, n_pairs = [], 0
    for i, gi in enumerate(geoms):
        if canceled():
            return None, None
        if feedback is not None:
            feedback.setProgress(40.0 + 30.0 * i / max(len(geoms), 1))
        for j in index.intersects(gi.boundingBox()):
            if j <= i or not gi.intersects(geoms[j]):
                continue
            n_pairs += 1
            a = gi.intersection(geoms[j]).area()
            if a > 0:
                overlaps.append({"a": t_ok[i], "b": t_ok[j], "area_m2": float(a)})

    step("Gaps: holes in the union of municipalities")
    gaps = []
    if geoms:
        union = QgsGeometry.unaryUnion(geoms)
        holes = list(_rings_of_holes(union))
        for h_i, hole in enumerate(holes):
            if canceled():
                return None, None
            if feedback is not None:
                feedback.setProgress(70.0 + 30.0 * h_i / max(len(holes), 1))
            zone = hole.buffer(1.0, BUFFER_SEGMENTS)
            touching = sorted(k for k in index.intersects(zone.boundingBox()) if zone.intersects(geoms[k]))
            bb = hole.boundingBox()
            gaps.append({"area_m2": float(hole.area()),
                         "bounds": [bb.xMinimum(), bb.yMinimum(), bb.xMaximum(), bb.yMaximum()],
                         "touching": [t_ok[k] for k in touching]})

    crs = source.sourceCrs()
    m = {
        "crs": crs.authid() if crs.isValid() and crs.authid() else None,
        "n_features": len(features),
        "features": features,
        "n_pairs_checked": n_pairs,
        "overlaps": overlaps,
        "gaps": gaps,
        "border": None,
    }
    return m, geometries
