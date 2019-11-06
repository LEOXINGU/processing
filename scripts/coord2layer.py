# -*- coding: utf-8 -*-

"""
coord2layer.py
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
__date__ = '2019-11-02'
__copyright__ = '(C) 2019, Leandro França'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import *
import processing


class CoordinatesToLayer(QgsProcessingAlgorithm):

    TABLE = 'TABLE'
    X = 'X'
    Y = 'Y'
    Z = 'Z'
    BOOL = 'BOOL'
    CRS = 'CRS'
    LAYER = 'LAYER'
    
    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CoordinatesToLayer()

    def name(self):
        return 'coord2layer'

    def displayName(self):
        return self.tr('Coordinates to Layer')

    def group(self):
        return self.tr('LF Surveyor')

    def groupId(self):
        return 'lf_surveyor'

    def shortHelpString(self):
        return self.tr("Generates a <b>point layer</b> from a coordinate table, whether it comes from a Microsoft <b>Excel</b> spreadsheet, Libre Office <b>Calc</b>, or even attributes from another layer.")

    def initAlgorithm(self, config=None):
        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TABLE,
                self.tr('Table of observations'),
                [QgsProcessing.TypeVector]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.X,
                self.tr('X Coordinate'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.Numeric
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.Y,
                self.tr('Y Coordinate'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.Numeric
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.Z,
                self.tr('Z Coordinate'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.Numeric
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.BOOL,
                self.tr('Create PointZ'),
                defaultValue=False))
        
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS, 
                self.tr('Grid CRS'), 
                'ProjectCrs'))
        
        # OUTPUT
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LAYER,
                self.tr('Adjusted Points')
            )
        )
    
    def processAlgorithm(self, parameters, context, feedback):

        table = self.parameterAsSource(
            parameters,
            self.TABLE,
            context
        )
        
        if table is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.TABLE))
        
        X_field = self.parameterAsFields(
            parameters,
            self.X,
            context
        )
        
        Y_field = self.parameterAsFields(
            parameters,
            self.Y,
            context
        )

        Z_field = self.parameterAsFields(
            parameters,
            self.Z,
            context
        )
        
        CreateZ = self.parameterAsBool(
            parameters,
            self.BOOL,
            context
        )
        
        CRS = self.parameterAsCrs(
            parameters,
            self.CRS,
            context
        )
        
        # Field index
        X_id = table.fields().indexFromName(X_field[0])
        Y_id = table.fields().indexFromName(Y_field[0])
        Z_id = table.fields().indexFromName(Z_field[0])
        
        # OUTPUT
        Fields = table.fields()
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.LAYER,
            context,
            Fields,
            QgsWkbTypes.Point,
            CRS
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.LAYER))
        
        feature = QgsFeature()
        total = 100.0 / table.featureCount() if table.featureCount() else 0
        for current, feat in enumerate(table.getFeatures()):
            att = feat.attributes()
            X = att[X_id]
            Y = att[Y_id]
            Z = att[Z_id]
            if CreateZ:
                geom = QgsGeometry(QgsPoint(float(X), float(Y), float(Z)))
            else:
                geom = QgsGeometry.fromPointXY(QgsPointXY(float(X), float(Y)))
            feature.setGeometry(geom)
            feature.setAttributes(att)
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
            if feedback.isCanceled():
                break
            feedback.setProgress(int(current * total))
            
        feedback.pushInfo(self.tr('Operation completed successfully!'))
        feedback.pushInfo('Leandro França - Eng Cart')
        
        return {self.LAYER: dest_id}
