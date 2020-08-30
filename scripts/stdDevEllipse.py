# -*- coding: utf-8 -*-

"""
stdDevEllipse.py
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
__date__ = '2020-08-22'
__copyright__ = '(C) 2020, Leandro França'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsPointXY,
                       QgsGeometry,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterField,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterEnum,
                       QgsFeatureRequest,
                       QgsExpression,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFileDestination,
                       QgsApplication,
                       QgsProject,
                       QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem)
import processing
import numpy as np
from numpy import pi, cos, sin, sqrt


class StdDevEllipse(QgsProcessingAlgorithm):

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

    def createInstance(self):
        return StdDevEllipse()

    def name(self):
        return 'stdellipse'

    def displayName(self):
        return self.tr('Directional Distribution', 'Distribuição Direcional')

    def group(self):
        return self.tr('LF Spatial Statistics', 'LF Estatística Espacial')

    def groupId(self):
        return 'lf_spatialstatistics'

    def shortHelpString(self):
        if self.LOC == 'pt':
            return "Cria elipses de desvio padrão para resumir as características espaciais de feções geográficos do tipo ponto: tendência central, dispersão e tendências direcionais."
        else:
            return self.tr("Creates standard deviational ellipses to summarize the spatial characteristics of point type geographic features: central tendency, dispersion, and directional trends.")
    
    INPUT = 'INPUT'
    TAM = 'TAM'
    PESO = 'PESO'
    CAMPO_PESO = 'CAMPO_PESO'
    AGRUPAR = 'AGRUPAR'
    CAMPO_AGRUPAR = 'CAMPO_AGRUPAR'
    OUTPUT = 'OUTPUT'
    
    def initAlgorithm(self, config=None):
        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Point Layer', 'Camada de Pontos'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        tipos = [self.tr('1 Standard Deviation (68%)', '1 Desvio-Padrão (68%)'),
                 self.tr('2 Standard Deviations (95%)', '2 Desvios-Padrões (95%)'),
                 self.tr('3 Standard Deviations (99.7%)', '3 Desvios-Padrões (99,7%)')]

        self.addParameter(
            QgsProcessingParameterEnum(
                self.TAM,
                self.tr('Size', 'Tamanho'),
				options = tipos,
                defaultValue= 0
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PESO,
                self.tr('Use Weight', 'Utilizar Peso'),
                defaultValue=True))
                
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.AGRUPAR,
                self.tr('Group by Attribute', 'Agrupar por Atributo'),
                defaultValue=True))
                
        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_PESO,
                self.tr('Weight Field (Optional)', 'Campo de Peso (Opcional)'),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Numeric
            )
        )
                
        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_AGRUPAR,
                self.tr('Group Field (Optional)', 'Campo de Agrupamento (Opcional)'),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Any
            )
        )

        # OUTPUT
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Standard Deviational Ellipse(s)', 'Elipse(s) de Distribuição')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        layer = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )
        if layer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
            
        size = self.parameterAsEnum(
            parameters,
            self.TAM,
            context
        )
        Tam = size+1
        
        Peso = self.parameterAsBool(
            parameters,
            self.PESO,
            context
        )
        
        Campo_Peso = self.parameterAsFields(
            parameters,
            self.CAMPO_PESO,
            context
        )
        
        Agrupar = self.parameterAsBool(
            parameters,
            self.AGRUPAR,
            context
        )
        
        Campo_Agrupar = self.parameterAsFields(
            parameters,
            self.CAMPO_AGRUPAR,
            context
        )

        # Field index
        Campo_Peso = layer.fields().indexFromName(Campo_Peso[0])
        Campo_Agrupar = layer.fields().indexFromName(Campo_Agrupar[0])

        # OUTPUT
        GeomType = QgsWkbTypes.Polygon
        Fields = QgsFields()
        CRS = layer.sourceCrs()
        itens  = {
             'id' : QVariant.Int,
             'group': QVariant.String,
             'avg_x' : QVariant.Double,
             'avg_y' : QVariant.Double,
             'n_std': QVariant.Int,
             'std_x' : QVariant.Double,
             'std_y' : QVariant.Double,
             'major_axis': QVariant.Double,
             'minor_axis': QVariant.Double
             }
        for item in itens:
            Fields.append(QgsField(item, itens[item]))
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            Fields,
            GeomType,
            CRS
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        if Agrupar:
            dic = {}
            for feat in layer.getFeatures():
                pnt = feat.geometry().asPoint()
                grupo = feat[Campo_Agrupar]
                if grupo in dic:
                    dic[grupo]['x'] = dic[grupo]['x'] + [pnt.x()]
                    dic[grupo]['y'] = dic[grupo]['y'] + [pnt.y()]
                    dic[grupo]['w'] = dic[grupo]['w'] + [int(feat[Campo_Peso])]
                else:
                    dic[grupo] = {'x':[pnt.x()], 'y':[pnt.y()], 'w':[int(feat[Campo_Peso])]}
        else:
            dic = {}
            for feat in layer.getFeatures():
                pnt = feat.geometry().asPoint()
                grupo = 'ungrouped'
                if grupo in dic:
                    dic[grupo]['x'] = dic[grupo]['x'] + [pnt.x()]
                    dic[grupo]['y'] = dic[grupo]['y'] + [pnt.y()]
                    dic[grupo]['w'] = dic[grupo]['w'] + [int(feat[Campo_Peso])]
                else:
                    dic[grupo] = {'x':[pnt.x()], 'y':[pnt.y()], 'w':[int(feat[Campo_Peso])]}
        
        feature = QgsFeature()
        total = 100.0 / len(dic) if len(dic) else 0
        for current, grupo in enumerate(dic):
            x = np.array(dic[grupo]['x'])
            y = np.array(dic[grupo]['y'])
            w = dic[grupo]['w']
            
            if len(x)==1:
                raise QgsProcessingException(self.tr("Invalid Group Field!","Campo de Agrupamento Inválido!"))
            
            if Peso:
                if (np.array(w) > 0).sum() > 1: # Mais de um ponto com peso maior que zero
                    MVC = np.cov(x,y, fweights = w)
                    mediaX = float(np.average(x, weights = w))
                    mediaY = float(np.average(y, weights = w))
                else:
                    continue
            else:
                MVC = np.cov(x,y)
                mediaX = float(np.average(x))
                mediaY = float(np.average(y))

            σ2x = MVC[0][0]
            σ2y = MVC[1][1]
            σ2xy = MVC[0][1]

            # Elipse de Erro para um determinado desvio-padrão
            # Centro da Elipse
            C=[mediaX, mediaY]
            # Auto valores e autovetores da MVC
            Val, Vet = np.linalg.eig(np.matrix(MVC))
            λ1 = Val[0]
            λ2 = Val[1]
            v1 = np.array(Vet[:,0]).reshape([1,2])
            v2 = np.array(Vet[:,1]).reshape([1,2])

            AtPA = Vet.T*MVC*Vet
            c1 = sqrt(AtPA[1,1]) # para x
            c2 = sqrt(AtPA[0,0]) # para y
             
            # Determinando os pontos da Elipse
            p = np.arange(0,2*pi,0.1)
            x_ell = Tam*c1*cos(p)
            y_ell = Tam*c2*sin(p)
            M1 = np.matrix([x_ell, y_ell])
            # Rotacionando phi de x e y
            if σ2x < σ2y:
                phi = np.arccos(np.dot(v2,[1,0]))[0]
            else:
                phi = pi - np.arccos(np.dot(v2,[1,0]))[0]

            rot = np.matrix([[cos(phi), sin(phi)], [-sin(phi), cos(phi)]])
            M2 = rot*M1
            X_ell = np.array(M2[0,:]) + C[0]
            Y_ell = np.array(M2[1,:]) + C[1]

            coord = []
            for k in range(len(X_ell[0])):
                coord += [QgsPointXY(float(X_ell[0,k]), float(Y_ell[0,k]))]
                
            pol = QgsGeometry.fromPolygonXY([coord + [coord[0]]])
            feat = QgsFeature(Fields)
            feat.setGeometry(pol)
            cont = 1
            if σ2x < σ2y:
                feat.setAttributes([cont, str(grupo), float(mediaX), float(mediaY), Tam, 
                                              float(x.std()),float(y.std()), 
                                              float(c1), float(c2)])
            else:
                feat.setAttributes([cont, str(grupo), float(mediaX), float(mediaY), Tam,
                                              float(x.std()),float(y.std()), 
                                              float(c2), float(c1)])
            
            sink.addFeature(feat, QgsFeatureSink.FastInsert)
            if feedback.isCanceled():
                break
            feedback.setProgress(int(current * total))
        
        feedback.pushInfo(self.tr('Operation completed successfully!', 'Operação finalizada com sucesso!'))
        feedback.pushInfo('Leandro França - Eng Cart')

        return {self.OUTPUT: dest_id}
