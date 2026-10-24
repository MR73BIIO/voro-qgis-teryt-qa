"""
Check municipality boundaries against TERC.

Checks C1-C7: C1 geometry, C2 TERYT, C3 nesting in counties, C4 CRS and extent,
C5 overlaps and gaps, C6 names vs TERC, C7 state border (only when the state layer is given).
Thresholds and known exceptions are the files params.json and known_exceptions.json
copied from voro-gis-qa, not set in the dialog.
"""
import configparser
import json
import os
from collections import Counter
from datetime import datetime

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsPointXY,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFile,
    QgsProcessingParameterFileDestination,
)
from qgis.PyQt.QtCore import QMetaType
from qgis.PyQt.QtGui import QIcon

from . import i18n, qa_checks, report
from .qa_measures import measure, read_geometries

HERE = os.path.dirname(__file__)
FINDING_FIELDS = ("check", "teryt", "severity", "detail")
CHECKS_IN_THIS_VERSION = ("C1", "C2", "C3", "C4", "C5", "C6", "C7")


def findings_fields():
    fields = QgsFields()
    for name in FINDING_FIELDS:
        fields.append(QgsField(name, QMetaType.Type.QString))
    return fields


def plugin_version():
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(HERE, "metadata.txt"), encoding="utf-8")
    return cfg.get("general", "version", fallback="?")


def load_json(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)


def poland_extent(expected_crs, transform_context):
    """Corners of the Poland bbox (lon/lat) transformed to the expected CRS -> (minx, miny, maxx, maxy)."""
    lon0, lat0, lon1, lat1 = qa_checks.PL_BBOX_LONLAT
    tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"),
                                QgsCoordinateReferenceSystem(expected_crs), transform_context)
    pts = [tr.transform(QgsPointXY(x, y)) for x, y in
           ((lon0, lat0), (lon1, lat0), (lon0, lat1), (lon1, lat1))]
    xs, ys = [p.x() for p in pts], [p.y() for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


class BoundaryQaAlgorithm(QgsProcessingAlgorithm):
    GMINY = "GMINY"
    GMINY_TERYT = "GMINY_TERYT"
    GMINY_NAME = "GMINY_NAME"
    POWIATY = "POWIATY"
    POWIATY_TERYT = "POWIATY_TERYT"
    TERC = "TERC"
    STATE = "STATE"
    KNOWN_UNCOVERED = "KNOWN_UNCOVERED"
    OUTPUT = "OUTPUT"
    REPORT = "REPORT"

    def tr(self, text):
        return i18n.tr(text)

    def createInstance(self):  # noqa: N802 (QGIS name)
        return BoundaryQaAlgorithm()

    def name(self):
        return "boundary_qa"

    def icon(self):
        return QIcon(os.path.join(HERE, "icon.png"))

    def displayName(self):  # noqa: N802 (QGIS name)
        return self.tr("Check boundaries against TERC")

    def shortHelpString(self):  # noqa: N802 (QGIS name)
        return i18n.help_text()

    def initAlgorithm(self, config=None):  # noqa: N802 (QGIS name)
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.GMINY, self.tr("Municipalities (gminy)"),
            [Qgis.ProcessingSourceType.VectorPolygon]))
        self.addParameter(QgsProcessingParameterField(
            self.GMINY_TERYT, self.tr("Municipality TERYT field"),
            defaultValue="teryt", parentLayerParameterName=self.GMINY))
        self.addParameter(QgsProcessingParameterField(
            self.GMINY_NAME, self.tr("Municipality name field"),
            defaultValue="name", parentLayerParameterName=self.GMINY))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.POWIATY, self.tr("Counties (powiaty)"),
            [Qgis.ProcessingSourceType.VectorPolygon]))
        self.addParameter(QgsProcessingParameterField(
            self.POWIATY_TERYT, self.tr("County TERYT field"),
            defaultValue="teryt", parentLayerParameterName=self.POWIATY))
        self.addParameter(QgsProcessingParameterFile(
            self.TERC, self.tr("TERC register (CSV)"), extension="csv"))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.STATE, self.tr("State border (optional, for C7)"),
            [Qgis.ProcessingSourceType.VectorPolygon], optional=True))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.KNOWN_UNCOVERED, self.tr("Known areas without municipalities, e.g. the sea (optional, for C7)"),
            [Qgis.ProcessingSourceType.VectorPolygon], optional=True))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT, self.tr("Findings")))
        self.addParameter(QgsProcessingParameterFileDestination(
            self.REPORT, self.tr("HTML report"), self.tr("HTML files (*.html)"),
            optional=True, createByDefault=False))

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802 (QGIS name)
        gminy = self.parameterAsSource(parameters, self.GMINY, context)
        if gminy is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.GMINY))
        powiaty = self.parameterAsSource(parameters, self.POWIATY, context)
        if powiaty is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.POWIATY))
        teryt_field = self.parameterAsString(parameters, self.GMINY_TERYT, context)
        powiaty_teryt_field = self.parameterAsString(parameters, self.POWIATY_TERYT, context)
        name_field = self.parameterAsString(parameters, self.GMINY_NAME, context)
        terc_path = self.parameterAsFile(parameters, self.TERC, context)
        if not terc_path or not os.path.isfile(terc_path):
            raise QgsProcessingException(self.tr("TERC file not found: {}").format(terc_path))

        params = load_json("params.json")
        exceptions = load_json("known_exceptions.json")
        try:
            terc = qa_checks.load_terc_gminy(terc_path)
        except Exception as e:  # noqa: BLE001
            raise QgsProcessingException(f"TERC: {e}") from e

        feedback.pushInfo(self.tr("Municipalities: {} | counties: {} | CRS: {} | TERC municipalities: {}").format(
            gminy.featureCount(), powiaty.featureCount(), gminy.sourceCrs().authid(), len(terc)))

        state = self.parameterAsSource(parameters, self.STATE, context)
        reference = self.parameterAsSource(parameters, self.KNOWN_UNCOVERED, context)
        state_geoms = ref_geoms = None
        if state is not None:
            if not state.sourceCrs().isValid():
                raise QgsProcessingException(self.tr("State border layer has no CRS"))
            if reference is not None and not reference.sourceCrs().isValid():
                raise QgsProcessingException(self.tr("Layer of known areas without municipalities has no CRS"))
            if gminy.sourceCrs().authid() == params["expected_crs"]:
                target = QgsCoordinateReferenceSystem(params["expected_crs"])
                state_geoms = read_geometries(state, target, context.transformContext())
                if reference is not None:
                    ref_geoms = read_geometries(reference, target, context.transformContext())
            else:
                feedback.pushInfo(self.tr("C7: state layer not used, the municipalities are not in {}").format(
                    params["expected_crs"]))
        elif reference is not None:
            feedback.pushInfo(self.tr("C7: known areas layer given without the state layer, C7 is skipped"))

        m, geometries = measure(gminy, teryt_field, name_field, terc,
                                powiaty, powiaty_teryt_field, feedback,
                                state=state_geoms, reference=ref_geoms)
        if m is None or feedback.isCanceled():
            return {}
        pl_extent = poland_extent(params["expected_crs"], context.transformContext())
        findings, diagnostics = qa_checks.judge(m, params, exceptions, pl_extent)

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, findings_fields(),
            Qgis.WkbType.MultiPolygon, gminy.sourceCrs())
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        geom_of = {}
        for f, g in zip(m["features"], geometries):
            geom_of.setdefault(f["teryt"], g)
        for fd in findings:
            feat = QgsFeature(findings_fields())
            feat.setAttributes([fd["check"], fd["teryt"], fd["severity"], fd["detail"]])
            g = geom_of.get(fd["teryt"]) if fd["teryt"] is not None else None
            if g is not None and not g.isNull():
                g = type(g)(g)
                g.convertToMultiType()
                feat.setGeometry(g)
            sink.addFeature(feat, QgsFeatureSink.Flag.FastInsert)

        per_check = Counter(fd["check"] for fd in findings)
        severities = {fd["severity"] for fd in findings}
        feedback.pushInfo(self.tr("Dataset status: {}").format(qa_checks.status_for(severities)))
        for c in CHECKS_IN_THIS_VERSION:
            feedback.pushInfo(self.tr("  {}: {} findings").format(c, per_check.get(c, 0)))
        feedback.pushInfo(self.tr("Diagnostics: {}").format(json.dumps(diagnostics, ensure_ascii=False)))
        feedback.pushInfo(self.tr("Findings total: {}").format(len(findings)))

        results = {self.OUTPUT: dest_id}
        report_path = self.parameterAsFileOutput(parameters, self.REPORT, context)
        if report_path:
            meta = {
                "Data kontroli": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Warstwa gmin": gminy.sourceName(),
                "Liczba gmin": m["n_features"],
                "Warstwa powiatów": powiaty.sourceName(),
                "Liczba powiatów": powiaty.featureCount(),
                "Układ współrzędnych": m["crs"] or "brak",
                "Plik TERC": os.path.basename(terc_path),
                "Gminy w TERC": len(terc),
                "Warstwa granicy państwa": state.sourceName() if state is not None else "brak (C7 pominięta)",
                "Znane obszary bez gmin": reference.sourceName() if reference is not None else "brak",
                "Wtyczka": f"VORO TERYT QA {plugin_version()}",
                "QGIS": Qgis.version(),
            }
            names = {}
            for f in m["features"]:
                names.setdefault(f["teryt"], f["name"])
            html = report.render(findings, diagnostics, qa_checks.status_for(severities),
                                 meta, names, params)
            with open(report_path, "w", encoding="utf-8") as fh:
                fh.write(html)
            feedback.pushInfo(self.tr("HTML report: {}").format(report_path))
            results[self.REPORT] = report_path
        return results
