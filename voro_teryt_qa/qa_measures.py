"""
MEASUREMENTS in PyQGIS - same schema as voro-gis-qa measures.measure() (544fbec).
No thresholds and no judgement here; that is done in qa_checks.

Per municipality: geometry, TERYT, name, TERC name, bounding box, parent county, distance
of a point on the surface to the parent county.
For the whole layer: overlaps between municipalities and gaps (holes in the union).
State border (C7, since v0.2): pieces of the state without municipalities and pieces of
municipalities outside the state, as voro-gis-qa measures.py; the sea as one reference piece.
"""
from qgis.core import Qgis, QgsCoordinateTransform, QgsFeatureRequest, QgsGeometry, QgsSpatialIndex

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


def _parts(geom):
    """Parts of a (multi)geometry as separate geometries; [] for an empty result."""
    if geom is None or geom.isNull() or geom.isEmpty():
        return []
    return geom.asGeometryCollection()


def _bounds(geom):
    if geom is None or geom.isNull() or geom.isEmpty():
        return None
    bb = geom.boundingBox()
    return [bb.xMinimum(), bb.yMinimum(), bb.xMaximum(), bb.yMaximum()]


def read_geometries(source, target_crs, transform_context):
    """All non-empty geometries of a layer, transformed to target_crs (QgsCoordinateReferenceSystem)."""
    transform = QgsCoordinateTransform(source.sourceCrs(), target_crs, transform_context)
    same = source.sourceCrs() == target_crs
    out = []
    for f in _read_all(source):
        g = QgsGeometry(f.geometry())
        if _empty(g):
            continue
        if not same:
            g.transform(transform)
        out.append(g)
    return out


def measure_border(union, geoms, t_ok, index, state, reference=None, canceled=None):
    """State border (C7), no thresholds - as voro-gis-qa measures.py (544fbec).
    state / reference: lists of QgsGeometry in the CRS of the municipalities.
    Pieces of the state without municipalities ('uncovered') and pieces of municipalities outside
    the state ('outside'). The known area without municipalities (the sea, from the reference layer)
    is ONE reference piece, so a new hole at the coast stays a separate piece (note_1.6)."""
    state_geom = QgsGeometry.unaryUnion(list(state))
    zone = QgsGeometry(state_geom.constGet().boundary()).buffer(1.0, BUFFER_SEGMENTS)
    zone_engine = QgsGeometry.createGeometryEngine(zone.constGet())
    zone_engine.prepareGeometry()
    border = []
    uncovered = state_geom.difference(union)
    if reference:
        ref_geom = QgsGeometry.unaryUnion(list(reference))
        in_ref = uncovered.intersection(ref_geom)
        border.append({"kind": "uncovered", "reference": True,
                       "area_m2": float(in_ref.area()),
                       "bounds": _bounds(in_ref),
                       "at_state_border": True, "touching": []})
        uncovered = uncovered.difference(ref_geom)
    for kind, diff in (("uncovered", uncovered), ("outside", union.difference(state_geom))):
        for piece in _parts(diff):
            if canceled is not None and canceled():
                return None
            if piece.isEmpty() or piece.area() <= 0:
                continue
            zone_p = piece.buffer(1.0, BUFFER_SEGMENTS)
            touching = sorted(k for k in index.intersects(zone_p.boundingBox()) if zone_p.intersects(geoms[k]))
            border.append({"kind": kind,
                           "area_m2": float(piece.area()),
                           "bounds": _bounds(piece),
                           "at_state_border": bool(zone_engine.intersects(piece.constGet())),
                           "touching": [t_ok[k] for k in touching]})
    return border


def measure(source, teryt_field, name_field, terc, powiaty, powiaty_teryt_field, feedback=None,
            state=None, reference=None):
    """Facts about the municipalities. Returns (m, geometries) where geometries[row] = QgsGeometry.
    state / reference: optional lists of QgsGeometry (state layer, known areas without
    municipalities) in the CRS of the municipalities; without state, C7 is not measured."""
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
    union = None
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

    border = None
    if state is not None and union is not None:
        step("State border")
        border = measure_border(union, geoms, t_ok, index, state, reference, canceled)
        if border is None:
            return None, None

    crs = source.sourceCrs()
    m = {
        "crs": crs.authid() if crs.isValid() and crs.authid() else None,
        "n_features": len(features),
        "features": features,
        "n_pairs_checked": n_pairs,
        "overlaps": overlaps,
        "gaps": gaps,
        "border": border,
    }
    return m, geometries
