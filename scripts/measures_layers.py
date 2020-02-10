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

    def tradutor(self, string):
        DIC_en_pt = {'Measure Layers': 'Medir Camadas',
                            'LF Effortlessness': 'LF Mão na roda',
                            'Meters (m)': 'Metros (m)',
                            'Square Meters (m²)': 'Metros quadrados (m²)',
                            'Distance Units': 'Unidade de distância',
                            'Area Units': 'Unidade de área',
                            'Precision': 'Número de casas decimais',
                            'length': 'comprimento',
                            'perimeter': 'perímetro',
                            'area': 'área',
                            'Feets (ft)': 'Pés (ft)',
                            'Yards (yd)': 'Jardas (yd)',
                            'Kilometers (Km)': 'Quilômetros (Km)',
                            'Miles (mi)': 'Milhas (mi)',
                            'Square Meters (m²)': 'Metros quadrados (m²)',
                            'Square Kilometers (Km²)': 'Quilômetros quadrados (Km²)'
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
        units_dist = [self.tr('Meters (m)'),
                      self.tr('Feets (ft)'),
                      self.tr('Yards (yd)'),
                      self.tr('Kilometers (Km)'),
                      self.tr('Miles (mi)')
               ]
        units_area = [self.tr('Square Meters (m²)'),
                      self.tr('Hectares (ha)'),
                      self.tr('Square Kilometers (Km²)')
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

        precisao = self.parameterAsInt(
            parameters,
            self.PRECISION,
            context
        )

        # Transformação de unidades
        unid_transf_dist = [1, 0.3048, 0.9144, 1000, 621.4]
        unid_abb_dist = ['m', 'ft', 'yd', 'Km', 'mi']
        unid_transf_area = [1.0, 1e4, 1e6]
        unid_abb_area = ['m²', 'ha', 'Km²']
        unidade_dist = unid_transf_dist[units_dist]
        unidade_area = unid_transf_area[units_area]

        field_length = QgsField( self.tr('length')+'_'+unid_abb_dist[units_dist], QVariant.Double, "numeric", 14, precisao)
        field_perimeter = QgsField( self.tr('perimeter')+'_'+unid_abb_dist[units_dist], QVariant.Double, "numeric", 14, precisao)
        field_area = QgsField( self.tr('area')+'_'+unid_abb_area[units_area], QVariant.Double, "numeric", 14, precisao)

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
                    layer.addExpressionField('$length'+'/'+str(unidade_dist), field_length)
                if layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                    layer.addExpressionField('$perimeter'+'/'+str(unidade_dist), field_perimeter)
                    layer.addExpressionField('$area'+'/'+str(unidade_area), field_area)
            feedback.setProgress(int(current * total))

        return {}
