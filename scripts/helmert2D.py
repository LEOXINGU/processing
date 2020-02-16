# -*- coding: utf-8 -*-

"""
helmert2D.py
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
__date__ = '2019-11-08'
__copyright__ = '(C) 2019, Leandro França'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import *
import numpy as np
from numpy.linalg import norm, inv, pinv, det


class Helmert2D(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    VECTOR = 'VECTOR'
    OUTPUT = 'OUTPUT'
    HTML = 'HTML'
    
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
        return Helmert2D()

    def name(self):
        return 'helmert2D'

    def displayName(self):
        return self.tr('2D Conformal Transformation', 'Transformação Conforme 2D')

    def group(self):
        return self.tr('LF Survey', 'LF Agrimensura')

    def groupId(self):
        return 'lf_survey'

    def shortHelpString(self):
        return self.tr("""two-dimensional conformal coordinate transformation, also known as the <i>four-parameter similarity transformation or Helmert 2D</i>, has the characteristic that true shape is retained after transformation. 
It is typically used in surveying when converting separate surveys into a common reference coordinate system.
This transformation is a three-step process that involves:<o:p></o:p></span></p>
<ul>
  <li><span style="" lang="EN-US"><b>Scaling</b>
to create equal dimensions in the two coordinate systems<o:p></o:p></span></li>
  <li><span style="" lang="EN-US"><b>Rotation</b>
to make the reference axes of the two systems parallel<o:p></o:p></span></li>
  <li><span style="" lang="EN-US"><b>Translations</b>
to create a common origin for the two coordinate systems<o:p></o:p></span></li></ul>
""")
    
    def transformPoint(self, pnt, a, b, c, d):
        X, Y = pnt.x(), pnt.y()
        Xt = X*a - Y*b + c
        Yt = X*b + Y*a + d
        return QgsPointXY(Xt, Yt)
        
    def transformGeom(self, geom, a, b, c, d):
        if geom.type() == 0: #Point
            if geom.isMultipart():
                pnts = geom.asMultiPoint()
                newPnts = []
                for pnt in pnts:
                    newPnts += [self.transformPoint(pnt, a, b, c, d)]
                newGeom = QgsGeometry.fromMultiPointXY(newPnts)
                return newGeom
            else:
                pnt = geom.asPoint()
                newPnt = self.transformPoint(pnt, a, b, c, d)
                newGeom = QgsGeometry.fromPointXY(newPnt)
                return newGeom
        elif geom.type() == 1: #Line
            if geom.isMultipart():
                linhas = geom.asMultiPolyline()
                newLines = []
                for linha in linhas:
                    newLine =[]
                    for pnt in linha:
                        newLine += [self.transformPoint(pnt, a, b, c, d)]
                    newLines += [newLine]
                newGeom = QgsGeometry.fromMultiPolylineXY(newLines)
                return newGeom
            else:
                linha = geom.asPolyline()
                newLine =[]
                for pnt in linha:
                    newLine += [self.transformPoint(pnt, a, b, c, d)]
                newGeom = QgsGeometry.fromPolylineXY(newLine)
                return newGeom
        elif geom.type() == 2: #Polygon
            if geom.isMultipart():
                poligonos = geom.asMultiPolygon()
                newPolygons = []
                for pol in poligonos:
                    newPol = []
                    for anel in pol:
                        newAnel = []
                        for pnt in anel:
                            newAnel += [self.transformPoint(pnt, a, b, c, d)]
                        newPol += [newAnel]
                    newPolygons += [newPol]
                newGeom = QgsGeometry.fromMultiPolygonXY(newPolygons)
                return newGeom
            else:
                pol = geom.asPolygon()
                newPol = []
                for anel in pol:
                    newAnel = []
                    for pnt in anel:
                        newAnel += [self.transformPoint(pnt, a, b, c, d)]
                    newPol += [newAnel]
                newGeom = QgsGeometry.fromPolygonXY(newPol)
                return newGeom
        else:
            return None
    
    def initAlgorithm(self, config=None):
        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input Vector Layer'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.VECTOR,
                self.tr('Two Points Vectors'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        # OUTPUT
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Transformed Layer')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFileDestination(
                'HTML',
                self.tr('Adjustment Report'),
                self.tr('HTML files (*.html)')
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):

        entrada = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )
        if entrada is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        
        deslc = self.parameterAsSource(
            parameters,
            self.VECTOR,
            context
        )
        if deslc is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.VECTOR))
        # Validação dos vetores de georreferenciamento
        if deslc.featureCount()<3:
            raise QgsProcessingException(self.tr('Number of vectors must be greater than two.'))
        for feat in deslc.getFeatures():
            geom = feat.geometry()
            coord = geom.asPolyline()
            if len(coord) != 2:
                raise QgsProcessingException(self.tr('Vectors must be exactly two points.'))
        
        # OUTPUT
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            entrada.fields(),
            entrada.wkbType(),
            entrada.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        html_output = self.parameterAsFileOutput(
            parameters, 
            self.HTML, 
            context
        )
        
        # Transformação Conforme
        '''
        Xt = X*a - Y*b + c
        Yt = X*b + Y*a + d
        a = S*cos(alfa)
        b = S*sin(alfa)
        '''
        # Lista de Pontos
        A = [] # Matriz Design
        L = [] # Transformed Coordinate A to B
        for feat in deslc.getFeatures():
            geom = feat.geometry()
            coord = geom.asPolyline()
            xa = coord[0].x()
            ya = coord[0].y()
            xb = coord[1].x()
            yb = coord[1].y()
            A += [[xa, -ya, 1, 0], [ya, xa, 0, 1]]
            L +=[[xb], [yb]]

        A = np.matrix(A)
        L = np.matrix(L)

        M = A.T*A
        if det(M):
            X = inv(M)*A.T*L
            
            a = X[0,0]
            b = X[1,0]
            c = X[2,0]
            d = X[3,0]

            theta = np.degrees(np.arctan2(b, a))
            if theta < 0:
                theta = 360 + theta

            S = a/abs(np.cos(np.radians(theta)))
        else:
            raise QgsProcessingException(self.tr('Georeferencing vectors should not be aligned.'))

        feature = QgsFeature()
        total = 100.0 / entrada.featureCount() if entrada.featureCount() else 0
        for current, feat in enumerate(entrada.getFeatures()):
            geom = feat.geometry()
            newgeom = self.transformGeom(geom, a, b, c, d)
            feature.setGeometry(newgeom)
            feature.setAttributes(feat.attributes())
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
            if feedback.isCanceled():
                break
            feedback.setProgress(int(current * total))
        
        texto_ini = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
  <title></title>
</head>
<body>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><u><span style=""
 lang="EN-US">Two Dimensional Conformal Coordinate
Transformation<o:p></o:p></span></u></b></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><i><span style="" lang="EN-US">ax
</span></i><i><span style="" lang="EN-US">-</span></i><i><span
 style="" lang="EN-US"> by </span></i><i><span
 style="" lang="EN-US">+</span></i><i><span
 style="" lang="EN-US"> Tx <span style="">&nbsp;</span>=
X </span></i><i><span style="" lang="EN-US">+</span></i><i><span
 style="" lang="EN-US"> Vx<o:p></o:p></span></i></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><i><span style="" lang="EN-US">bx
</span></i><i><span style="" lang="EN-US">+</span></i><i><span
 style="" lang="EN-US"> ay </span></i><i><span
 style="">+</span></i><i><span style=""
 lang="EN-US"> Ty = Y </span></i><i><span
 style="">+</span></i><i><span style=""
 lang="EN-US"> Vy<o:p></o:p></span></i></p>
<p class="MsoNormal"><span style="" lang="EN-US"><o:p>&nbsp;</o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span style="" lang="EN-US">Residual
Errors of Control Points<o:p></o:p></span></b></p>
<div align="center">
<table class="MsoTableGrid"
 style="border: medium none ; border-collapse: collapse;"
 border="0" cellpadding="0" cellspacing="0">
  <tbody>
    <tr style="">
      <td style="padding: 0cm 5.4pt; width: 84.9pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><i><span style="" lang="EN-US">POINT<o:p></o:p></span></i></p>
      </td>
      <td style="padding: 0cm 5.4pt; width: 84.95pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><i><span style="" lang="EN-US">Vx<o:p></o:p></span></i></p>
      </td>
      <td style="padding: 0cm 5.4pt; width: 84.95pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><i><span style="" lang="EN-US">Vy<o:p></o:p></span></i></p>
      </td>
    </tr>'''

        tabela = '''
    <tr style="">
      <td style="padding: 0cm 5.4pt; width: 84.9pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">[ID]<o:p></o:p></span></p>
      </td>
      <td style="padding: 0cm 5.4pt; width: 84.95pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">[Vx]<o:p></o:p></span></p>
      </td>
      <td style="padding: 0cm 5.4pt; width: 84.95pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">[Vy]<o:p></o:p></span></p>
      </td>
    </tr>'''
        texto_final ='''
  </tbody>
</table>
</div>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="" lang="EN-US"><o:p>&nbsp;</o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span style="" lang="EN-US">Transformation
Parameters:<o:p></o:p></span></b></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="" lang="EN-US">a
</span><span style="" lang="EN-US">=</span><span
 style="" lang="EN-US"> [a]<o:p></o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="" lang="EN-US">b
</span><span style="" lang="EN-US">= [b]</span><span
 style="" lang="EN-US"><o:p></o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="" lang="EN-US">Tx
</span><span style="" lang="EN-US">= [c]</span><span
 style="" lang="EN-US"><o:p></o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="" lang="EN-US">Ty
</span><span style="" lang="EN-US">= [d]</span><span
 style="" lang="EN-US"><o:p></o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span style="" lang="EN-US">Rotation</span></b><span
 style="" lang="EN-US"> =</span><span style=""
 lang="EN-US"> [theta]</span><span style=""
 lang="EN-US"><o:p></o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span style="" lang="EN-US">Scale</span></b><span
 style="" lang="EN-US"> </span><span style=""
 lang="EN-US">= [S]</span><span style=""
 lang="EN-US"><o:p></o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span style="" lang="EN-US">Adjustment&rsquo;s
Reference Variance</span></b><span style=""
 lang="EN-US"> <span style="">&nbsp;</span>=
</span><span style="">[sigma]</span><span
 style="" lang="EN-US"><o:p></o:p></span></p>
Leandro Fran&ccedil;a<br>
Cartographic Engineer<br>
<span
 style="font-size: 11pt; line-height: 107%; font-family: &quot;Calibri&quot;,sans-serif;"><a
 href="mailto:geoleandro.franca@gmail.com">geoleandro.franca@gmail.com</a></span><br>
</body>
</html>
'''

        texto = texto_ini

        # Calculo de Residuos
        transf = []
        for feat in deslc.getFeatures():
            geom = feat.geometry()
            coord = geom.asPolyline()
            Xt, Yt = self.transformPoint(coord[0], a, b, c, d)
            transf += [[Xt],[Yt]]
            X, Y = coord[-1].x(), coord[-1].y()
            Vx = X - Xt
            Vy = Y - Yt
            tableRowN = tabela
            itens  = {'[ID]' : str(feat.id()),
                         '[Vx]' : '{:.4f}'.format(float(Vx)),
                         '[Vy]' : '{:.4f}'.format(float(Vy)),
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            texto += tableRowN

        # Residuos
        V = L - np.matrix(transf)
        # Sigma posteriori
        n = np.shape(A)[0] # número de observações
        u = np.shape(A)[1] # número de parâmetros
        sigma2 = V.T*V/(n-u)

        # Dados finais
        itens  = {
                     '[a]' : str(a),
                     '[b]': str(b),
                     '[c]': str(c),
                     '[d]': str(d),
                     '[theta]': str(theta),
                     '[S]': str(S),
                     '[sigma]': str(sigma2[0,0])
                     }
        for item in itens:
                texto_final = texto_final.replace(item, itens[item])

        texto += texto_final

        # Exportar HTML
        arq = open(html_output, 'w')
        arq.write(texto)
        arq.close()
        
        feedback.pushInfo(self.tr('\nOperation completed successfully!'))
        feedback.pushInfo('Leandro França - Eng Cart\n')
        return {self.OUTPUT: dest_id,
                    self.HTML: html_output}