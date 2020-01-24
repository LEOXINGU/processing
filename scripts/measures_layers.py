# -*- coding: utf-8 -*-

"""
measures_layers.py
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
__date__ = '2019-10-06'
__copyright__ = '(C) 2020, Leandro França'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import *

class MeasureLayers(QgsProcessingAlgorithm):

    DISTANCE = 'DISTANCE'
    AREA = 'AREA'
    PRECISION = 'PRECISION'
    LOC = QgsApplication.locale()

    def tr(self, string):
        return QCoreApplication.translate('Processing', self.tradutor(string))
        
    def tradutor(self, string):
        DIC_en_pt = {'Measure Layers': 'Medir Camadas',
                            'LF Effortlessness': 'LF Mão na roda',
                            'Meters (m)': 'Metros (m)',
                            'Square Meters (m²)': 'Metros quadrados (m²)',
                            'Distance Units': 'Unidade de distância',
                            'Area Units': 'Unidade de área',
                            'Precision': 'Número de casas decimais'
                            }
        if self.LOC == 'pt':
            if string in DIC_en_pt:
                return DIC_en_pt[string]
            else:
                return string
        else:
            return string

    def createInstance(self):
        return MeasureLayers()

    def name(self):
        return 'measure_layers'

    def displayName(self):
        return self.tr('Measure Layers')

    def group(self):
        return self.tr('LF Effortlessness')

    def groupId(self):
        return 'lf_effortlessness'

    def shortHelpString(self):
        if self.LOC == 'pt':
            return "Esta ferramenta calcula em campos virtuais os comprimentos de feições do tipo linha e o perímetro e área de feições do tipo polígono para todas as camadas."
        else:
            return self.tr("This tool calculates in virtual fields the lengths of features of the line type and the perimeter and area of features of the polygon type for all layers.")
        
    def initAlgorithm(self, config=None):
        units_dist = [self.tr('Meters (m)')
               ]
        units_area = [self.tr('Square Meters (m²)')
               ]
               
        self.addParameter(
            QgsProcessingParameterEnum(
                self.DISTANCE,
                self.tr('Distance Units'),
				options = units_dist,
                defaultValue= 0
            )
        )
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.AREA,
                self.tr('Area Units'),
				options = units_area,
                defaultValue= 0
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PRECISION,
                self.tr('Precision'),
                type = 0, # float = 1 and integer = 0
                defaultValue = 3
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        units_dist = self.parameterAsEnum(
            parameters,
            self.DISTANCE,
            context
        )
        
        units_area = self.parameterAsEnum(
            parameters,
            self.AREA,
            context
        )
        
        # Transformação de unidades
        unid_transf = [1.0]
        unidade_dist = unid_transf[units_dist]
        unidade_area = unid_transf[units_dist]**2
        
        field_length = QgsField( 'length', QVariant.Double, "numeric", 14, 3)
        field_perimeter = QgsField( 'perimeter', QVariant.Double, "numeric", 14, 3)
        field_area = QgsField( 'area', QVariant.Double, "numeric", 14, 3)
        
        camadas = [layer.name() for layer in QgsProject.instance().mapLayers().values()]
        num_camadas = len(camadas)
        total = 100.0 / num_camadas if num_camadas else 0
        
        layers = QgsProject.instance().mapLayers()
        for current, layer in enumerate(layers.values()):
            if feedback.isCanceled():
                break
            # check the layer type
            if layer.type()==0:# VectorLayer
                # check the layer geometry type
                if layer.geometryType() == QgsWkbTypes.LineGeometry:
                    layer.addExpressionField('$length'+'*'+str(unidade_dist), field_length)
                if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                    layer.addExpressionField('$perimeter'+'*'+str(unidade_dist), field_perimeter)
                    layer.addExpressionField('$area'+'*'+str(unidade_area), field_area)
            feedback.setProgress(int(current * total))
        
        return {}