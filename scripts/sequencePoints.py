# -*- coding: utf-8 -*-


"""
sequencePoints.py
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
__author__ = 'Leandro França'
__date__ = '2020-06-11'
__copyright__ = '(C) 2020, Leandro França'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsApplication,
                       QgsProcessingParameterVectorLayer,
                       QgsGeometry,
                       QgsProcessing,
                       QgsProcessingParameterField,
                       QgsProcessingParameterBoolean,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink)


class SequencePoints(QgsProcessingAlgorithm):
    POINTS = 'POINTS'
    POLYGONS = 'POLYGONS'
    FIELD = 'FIELD'
    SAVE = 'SAVE'
    LOC = QgsApplication.locale()
    
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def translate(self, string):
        return QCoreApplication.translate('Processing', string)

    def tr(self, *string):
        # Traduzir para o portugês: arg[0] - english (translate), arg[1] - português
        if self.LOC == 'pt':
            if len(string) == 2:
                return string[1]
            else:
                return self.translate(string[0])
        else:
            return self.translate(string[0])

    def createInstance(self):
        return SequencePoints()

    def name(self):
        return 'sequencepoints'

    def displayName(self):
        return self.tr('Sequence Points', 'Sequenciar Pontos')

    def group(self):
        return self.tr('LF Vector', 'LF Vetor')

    def groupId(self):
        return 'lf_vector'

    def shortHelpString(self):
        return self.tr("This script fills a certain attribute of the features of a layer of points according to its sequence in relation to the polygon of another layer.", "Este script preenche um determinado atributo das feições de uma camada de pontos de acordo com sua sequência em relação ao polígono de outra camada.")

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.POINTS,
                self.tr('Points', 'Pontos'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD,
                self.tr('Sequence Field', 'Campo de ordenação dos vértices'),
                parentLayerParameterName=self.POINTS,
                type=QgsProcessingParameterField.Numeric
            )
        )
        
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.POLYGONS,
                self.tr('Polygon', 'Polígono'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SAVE,
                self.tr('Save Editions', 'Salvar Edições'),
                defaultValue=False
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):

        pontos = self.parameterAsVectorLayer(
            parameters,
            self.POINTS,
            context
        )
        if pontos is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.POINTS))
        
        poligonos = self.parameterAsVectorLayer(
            parameters,
            self.POLYGONS,
            context
        )
        if poligonos is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.POLYGONS))
        
        campo = self.parameterAsFields(
            parameters,
            self.FIELD,
            context
        )
        if poligonos is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.FIELD))
        
        columnIndex = pontos.fields().indexFromName(campo[0])
        
        pontos.startEditing() # coloca no modo edição
        total = 100.0 / poligonos.featureCount() if poligonos.featureCount() else 0
        
        for current, pol in enumerate(poligonos.getFeatures()):
            cont = 0
            geom = pol.geometry()
            if geom.isMultipart():
                coords = geom.asMultiPolygon()[0][0]
            else:
                coords = geom.asPolygon()[0]
            for vertice in coords[:-1]:
                vertice_geom = QgsGeometry.fromPointXY(vertice)
                for pnt in pontos.getFeatures():
                    pnt_geom = pnt.geometry()
                    if vertice_geom.intersects(pnt_geom):
                        cont += 1
                        pontos.changeAttributeValue(pnt.id(), columnIndex, cont)
            feedback.setProgress(int(current * total))
        
        salvar = self.parameterAsBool(
            parameters,
            self.SAVE,
            context
        )
        if salvar is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.SAVE))
        
        if salvar:
            pontos.commitChanges() # salva as edições
        
        return {}