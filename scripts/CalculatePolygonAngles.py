# -*- coding: utf-8 -*-

"""
calculatePolygonAngles.py
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

from PyQt5.QtCore import *
from qgis.core import *
from math import atan, pi, sqrt
import math
from numpy import floor


class CalculatePolygonAngles(QgsProcessingAlgorithm):

    POLYGONS = 'POLYGONS'
    ANGLES = 'ANGLES'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CalculatePolygonAngles()

    def name(self):
        return 'calculatepolygonangles'

    def displayName(self):
        return self.tr('Calculate Polygon Angles')

    def group(self):
        return self.tr('LF Vector')

    def groupId(self):
        return 'lf_vector'

    def shortHelpString(self):
        return self.tr("""This algorithm calculates the inner and outer angles of the polygon vertices of a layer.
The output layer corresponds to the points with the calculated angles stored in the respective attributes.""")

    def initAlgorithm(self, config=None):
        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POLYGONS,
                self.tr('Polygon layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        
        # OUTPUT
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ANGLES,
                self.tr('Points with angles')
            )
        )
    
    def azimute(self, A,B):
            # Cálculo dos Azimutes entre dois pontos (Vetor AB origem A extremidade B)
            if ((B.x()-A.x())>=0 and (B.y()-A.y())>0): #1º quadrante
                AzAB=atan((B.x()-A.x())/(B.y()-A.y()))
                AzBA=AzAB+pi
            elif ((B.x()-A.x())>0 and(B.y()-A.y())<0): #2º quadrante
                AzAB=pi+atan((B.x()-A.x())/(B.y()-A.y()))
                AzBA=AzAB+pi
            elif ((B.x()-A.x())<=0 and(B.y()-A.y())<0): #3º quadrante
                AzAB=atan((B.x()-A.x())/(B.y()-A.y()))+pi
                AzBA=AzAB-pi
            elif ((B.x()-A.x())<0 and(B.y()-A.y())>0): #4º quadrante
                AzAB=2*pi+atan((B.x()-A.x())/(B.y()-A.y()))
                AzBA=AzAB+pi
            elif ((B.x()-A.x())>0 and(B.y()-A.y())==0): # no eixo positivo de x (90º)
                AzAB=pi/2
                AzBA=1.5*pi
            else: # ((B.x()-A.x())<0 and(B.y()-A.y())==0) # no eixo negativo de x (270º)
                AzAB=1.5*pi
                AzBA=pi/2
            # Correção dos ângulos para o intervalo de 0 a 2pi
            if AzAB<0 or AzAB>2*pi:
                if (AzAB<0):
                   AzAB=AzAB+2*pi
                else:
                   AzAB=AzAB-2*pi
            if AzBA<0 or AzBA>2*pi:
                if (AzBA<0):
                    AzBA=AzBA+2*pi
                else:
                    AzBA=AzBA-2*pi
            return (AzAB, AzBA)

    def dd2dms(self, dd, n_digits=1):
        if dd != 0:
            graus = int(floor(abs(dd)))
            resto = abs(dd) - graus
            if dd < 0:
                texto = '-' + str(graus) + '°'
            else:
                texto = str(graus) + '°'
            minutos = int(floor(60*resto))
            resto = round(resto*60 - minutos, 10)
            texto = texto + '{:02d}'.format(minutos) + "'"
            segundos = resto*60
            if round(segundos,n_digits) == 60.0:
                minutos += 1
                segundos = 0
            if minutos == 60:
                graus += 1
                minutos = 0
            if n_digits < 1:
                texto = texto + '{:02d}'.format(int(segundos)) + '"'
            else:
                texto = texto + ('{:0' + str(3+n_digits) + '.' + str(n_digits) + 'f}').format(segundos) + '"'
            return texto
        else:
            return "0°00'" + ('{:0' + str(3+n_digits) + '.' + str(n_digits) + 'f}').format(0)
    
    def areaGauss(self, coord):
        soma = 0
        tam = len(coord)
        for k in range(tam):
            P1 = coord[ -1 if k==0 else k-1]
            P2 = coord[k]
            P3 = coord[ 0 if k==(tam-1) else (k+1)]
            soma += P2.x()*(P1.y() - P3.y())
        return soma/2
        
    def processAlgorithm(self, parameters, context, feedback):
        # INPUT
        source = self.parameterAsSource(
            parameters,
            self.POLYGONS,
            context
        )
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.POLYGONS))
        
        # OUTPUT
        # Camada de Saída
        GeomType = QgsWkbTypes.Point
        Fields = QgsFields()
        CRS = source.sourceCrs()

        itens  = {
                     'ord' : QVariant.Int,
                     'ang_inner_dd' : QVariant.Double,
                     'ang_inner' : QVariant.String,
                     'ang_outer_dd' : QVariant.Double,
                     'ang_outer' : QVariant.String,
                     }
        for item in itens:
            Fields.append(QgsField(item, itens[item]))
            
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.ANGLES,
            context,
            Fields,
            GeomType,
            source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.ANGLES))

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        fet = QgsFeature()
        for current, pol in enumerate(source.getFeatures()):
            geom = pol.geometry()
            if geom.isMultipart():
                coord = geom.asMultiPolygon[0][0] # Primeiro polígono e primeiro anel
            else:
                coord = geom.asPolygon()[0] # Primeiro anel
            AreaGauss = self.areaGauss(coord[:-1])
            tam = len(coord[:-1])
            cont = 0
            pntsDic = {}
            for ponto in coord[:-1]:
                cont += 1
                pntsDic[cont] = {'pnt': ponto}
            # Cálculo dos Ângulos Internos e Externos
            for k in range(tam):
                P1 = pntsDic[ tam if k==0 else k]['pnt']
                P2 = pntsDic[k+1]['pnt']
                P3 = pntsDic[ 1 if (k+2)==(tam+1) else (k+2)]['pnt']
                alfa = self.azimute(P2, P1)[0] - self.azimute(P2,P3)[0]
                alfa = alfa if alfa > 0 else alfa+2*pi
                if AreaGauss > 0: # sentido horário
                    pntsDic[k+1]['alfa_int'] = alfa*180/pi
                    pntsDic[k+1]['alfa_ext'] = 360 - alfa*180/pi
                else: # sentido anti-horário
                    pntsDic[k+1]['alfa_ext'] = alfa*180/pi
                    pntsDic[k+1]['alfa_int'] = 360 - alfa*180/pi
            # Carregando ângulos internos na camada
            for ponto in pntsDic:
                fet.setGeometry(QgsGeometry.fromPointXY(pntsDic[ponto]['pnt']))
                fet.setAttributes([ponto,
                                        pntsDic[ponto]['alfa_int'],
                                        self.dd2dms(pntsDic[ponto]['alfa_int']),
                                        pntsDic[ponto]['alfa_ext'],
                                        self.dd2dms(pntsDic[ponto]['alfa_ext']),
                                        ])
                sink.addFeature(fet, QgsFeatureSink.FastInsert)
                
                if feedback.isCanceled():
                    break
                feedback.setProgress(int(current * total))
        
        feedback.pushInfo(self.tr('Operation completed successfully!'))
        feedback.pushInfo('<b>Leandro França - Eng Cart</b>')
        return {self.ANGLES: dest_id}
