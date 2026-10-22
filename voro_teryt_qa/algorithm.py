"""
Check municipality boundaries against TERC.

Stage 1: skeleton. Inputs and the findings layer are in place,
the checks C1-C6 are not. The algorithm reads the inputs, reports counts
and returns an empty findings layer.
"""
import os

from qgis.core import (
    Qgis,
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFile,
)
from qgis.PyQt.QtCore import QCoreApplication, QMetaType

FINDING_FIELDS = ("check", "teryt", "severity", "detail")


def findings_fields():
    fields = QgsFields()
    for name in FINDING_FIELDS:
        fields.append(QgsField(name, QMetaType.Type.QString))
    return fields


class BoundaryQaAlgorithm(QgsProcessingAlgorithm):
    GMINY = "GMINY"
    GMINY_TERYT = "GMINY_TERYT"
    GMINY_NAME = "GMINY_NAME"
    POWIATY = "POWIATY"
    POWIATY_TERYT = "POWIATY_TERYT"
    TERC = "TERC"
    OUTPUT = "OUTPUT"

    def tr(self, text):
        return QCoreApplication.translate("BoundaryQaAlgorithm", text)

    def createInstance(self):  # noqa: N802 (QGIS name)
        return BoundaryQaAlgorithm()

    def name(self):
        return "boundary_qa"

    def displayName(self):  # noqa: N802 (QGIS name)
        return self.tr("Check boundaries against TERC")

    def shortHelpString(self):  # noqa: N802 (QGIS name)
        return self.tr(
            "Checks municipality polygons (PRG) against county polygons and the TERC register. "
            "Output: one row per finding with the fields check, teryt, severity, detail.\n\n"
            "Early version: the checks are not in yet, the output layer is empty."
        )

    def initAlgorithm(self, config=None):  # noqa: N802 (QGIS name)
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.GMINY, self.tr("Municipalities (gminy)"),
            [QgsProcessing.SourceType.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterField(
            self.GMINY_TERYT, self.tr("Municipality TERYT field"),
            defaultValue="teryt", parentLayerParameterName=self.GMINY))
        self.addParameter(QgsProcessingParameterField(
            self.GMINY_NAME, self.tr("Municipality name field"),
            defaultValue="name", parentLayerParameterName=self.GMINY))
        self.addParameter(QgsProcessingParameterFeatureSource(
            self.POWIATY, self.tr("Counties (powiaty)"),
            [QgsProcessing.SourceType.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterField(
            self.POWIATY_TERYT, self.tr("County TERYT field"),
            defaultValue="teryt", parentLayerParameterName=self.POWIATY))
        self.addParameter(QgsProcessingParameterFile(
            self.TERC, self.tr("TERC register (CSV)"), extension="csv"))
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.OUTPUT, self.tr("Findings")))

    def processAlgorithm(self, parameters, context, feedback):  # noqa: N802 (QGIS name)
        gminy = self.parameterAsSource(parameters, self.GMINY, context)
        if gminy is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.GMINY))
        powiaty = self.parameterAsSource(parameters, self.POWIATY, context)
        if powiaty is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.POWIATY))
        terc_path = self.parameterAsFile(parameters, self.TERC, context)
        if not terc_path or not os.path.isfile(terc_path):
            raise QgsProcessingException(self.tr("TERC file not found: {}").format(terc_path))

        sink, dest_id = self.parameterAsSink(
            parameters, self.OUTPUT, context, findings_fields(),
            Qgis.WkbType.MultiPolygon, gminy.sourceCrs())
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        feedback.pushInfo(f"Municipalities: {gminy.featureCount()}")
        feedback.pushInfo(f"Counties: {powiaty.featureCount()}")
        feedback.pushInfo(f"CRS: {gminy.sourceCrs().authid()}")
        feedback.pushInfo(f"TERC: {terc_path}")
        feedback.pushInfo("Stage 1 skeleton: no checks yet, 0 findings.")
        sink.flushBuffer()
        return {self.OUTPUT: dest_id}
