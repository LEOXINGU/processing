# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
# CalculoAreaPerimetro.py

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFileDestination,
                       QgsApplication,
                       QgsProject,
                       QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem)
from math import atan, pi, sqrt, floor
import math

class CalculoAreaPerimitro(QgsProcessingAlgorithm):

    PONTOLIMITE = 'PONTOLIMITE'
    AREAIMOVEL = 'AREAIMOVEL'
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
        return CalculoAreaPerimitro()

    def name(self):
        return 'calculateareaperimeter'

    def displayName(self):
        return self.tr('Area and Perimeter Report', 'Relatório de Área e Perímetro')

    def group(self):
        return self.tr('LF Documents', 'LF Documentos')

    def groupId(self):
        return 'lf_documents'

    def shortHelpString(self):
        return self.tr('This tool performs the Analytical Calculation of Area, Azimuths, Sides, UTM Projected and Geodetic Coordinates of a Property.', 'Esta ferramenta realiza o Cálculo Analítico de Área, Azimutes, Lados, Coordenadas Planas e Geodésicas de um Imóvel.')

    def initAlgorithm(self, config=None):
        
        # 'INPUTS'
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PONTOLIMITE,
                self.tr('Boundary Survey Points', 'Pontos de Limite'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.AREAIMOVEL,
                self.tr('Property Polygon', 'Área do Imóvel'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        # 'OUTPUTS'
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.HTML,
                self.tr('Analytical Calculation Results', 'Resultados do Cálculo Analítico'),
                self.tr('HTML files (*.html)')
            )
        )
    
    # Acentos para HTML
    def str2HTML(self, texto):
        if texto:
            dicHTML = {'Á': '&Aacute;',	'á': '&aacute;',	'Â': '&Acirc;',	'â': '&acirc;',	'À': '&Agrave;',	'à': '&agrave;',	'Å': '&Aring;',	'å': '&aring;',	'Ã': '&Atilde;',	'ã': '&atilde;',	'Ä': '&Auml;',	'ä': '&auml;',	'Æ': '&AElig;',	'æ': '&aelig;',	'É': '&Eacute;',	'é': '&eacute;',	'Ê': '&Ecirc;',	'ê': '&ecirc;',	'È': '&Egrave;',	'è': '&egrave;',	'Ë': '&Euml;',	'ë': '&Euml;',	'Ð': '&ETH;',	'ð': '&eth;',	'Í': '&Iacute;',	'í': '&iacute;',	'Î': '&Icirc;',	'î': '&icirc;',	'Ì': '&Igrave;',	'ì': '&igrave;',	'Ï': '&Iuml;',	'ï': '&iuml;',	'Ó': '&Oacute;',	'ó': '&oacute;',	'Ô': '&Ocirc;',	'ô': '&ocirc;',	'Ò': '&Ograve;',	'ò': '&ograve;',	'Ø': '&Oslash;',	'ø': '&oslash;',	'Ù': '&Ugrave;',	'ù': '&ugrave;',	'Ü': '&Uuml;',	'ü': '&uuml;',	'Ç': '&Ccedil;',	'ç': '&ccedil;',	'Ñ': '&Ntilde;',	'ñ': '&ntilde;',	'Ý': '&Yacute;',	'ý': '&yacute;',	'"': '&quot;', '”': '&quot;',	'<': '&lt;',	'>': '&gt;',	'®': '&reg;',	'©': '&copy;',	'\'': '&apos;', 'ª': '&ordf;', 'º': '&ordm', '°':'&deg;'}
            for item in dicHTML:
                if item in texto:
                    texto = texto.replace(item, dicHTML[item])
            return texto
        else:
            return ''

    # Fuso e Hemisfério
    def FusoHemisf(self, pnt):
        lon = pnt.x()
        lat = pnt.y()
        # Calculo do Fuso
        fuso = round((183+lon)/6.0)
        # Hemisferio
        hemisf = 'N' if lat>= 0 else 'S'
        return (hemisf, fuso)

    # Cálculo de Azimutes
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


    # Graus Decimais para DMS
    def dd2dms(self, dd, n_digits):
        if dd != 0:
            graus = int(floor(abs(dd)))
            resto = round(abs(dd) - graus, 10)
            if dd < 0:
                texto = '-' + str(graus) + '°'
            else:
                texto = str(graus) + '°'
            minutos = int(floor(60*resto))
            resto = round(resto*60 - minutos, 10)
            texto = texto + '{:02d}'.format(minutos) + "'"
            segundos = resto*60
            if n_digits < 1:
                texto = texto + '{:02d}'.format(int(segundos)) + '"'
            else:
                texto = texto + ('{:0' + str(3+n_digits) + '.' + str(n_digits) + 'f}').format(segundos) + '"'
            return texto
        else:
            return "0°00'" + ('{:0' + str(3+n_digits) + '.' + str(n_digits) + 'f}').format(0)
    
    
    def processAlgorithm(self, parameters, context, feedback):
        
        vertices = self.parameterAsSource(parameters,
                                                     self.PONTOLIMITE,
                                                     context)
        area = self.parameterAsSource(parameters,
                                                     self.AREAIMOVEL,
                                                     context)
                                                     
        if vertices is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.PONTOLIMITE))
        if area is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.AREAIMOVEL))
        
        # Pegando o SRC do Projeto
        SRC = QgsProject.instance().crs().description()
        
        # Verificando o SRC do Projeto
        if QgsProject.instance().crs().isGeographic():
            raise QgsProcessingException(self.tr('The Project CRS must be projected!', 'O SRC do Projeto deve ser Projetado!'))
        feedback.pushInfo(self.tr('Project CRS is {}.', 'SRC do Projeto é {}.').format(SRC))
        
        # Transformar Coordenadas de Geográficas para o sistema UTM
        coordinateTransformer = QgsCoordinateTransform()
        coordinateTransformer.setDestinationCrs(QgsProject.instance().crs())
        coordinateTransformer.setSourceCrs(QgsCoordinateReferenceSystem('EPSG:4674'))
        
        # Dados do levantamento
        #Fields = area.fields()
        #fieldnames = [field.name() for field in Fields]
        for feat in area.getFeatures():
                feat1 = feat
                break
        
        INICIO = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
  <title>C&aacute;lculo Anal&iacute;tico de
&Aacute;rea e Per&iacute;metro</title>
</head>
<body>
<div style="text-align: center;"><big><big><span
 style="font-weight: bold;">C&aacute;lculo
Anal&iacute;tico de &Aacute;rea, Azimutes, Lados, Coordenadas
Planas e Geod&eacute;sicas</span><br
 style="font-weight: bold;">
</big></big>
<div style="text-align: left;"><br>
<span style="font-weight: bold;">Im&oacute;vel:</span>
[IMOVEL]<br>
<span style="font-weight: bold;">Munic&iacute;pio:</span>
[MUNICIPIO] - [UF]<br style="font-weight: bold;">
<span style="font-weight: bold;">SGR:</span>
SIRGAS2000<br>
<span style="font-weight: bold;">Proje&ccedil;&atilde;o:</span>
[UTM] <br>
</div>
</div>
<table style="text-align: center; width: 100%;" border="1"
 cellpadding="0" cellspacing="0">
  <tbody>
    <tr>
      <td style="text-align: center; font-weight: bold;">Esta&ccedil;&atilde;o</td>
      <td style="text-align: center; font-weight: bold;">Vante</td>
      <td style="text-align: center; font-weight: bold;">Este (m)</td>
      <td style="text-align: center; font-weight: bold;">Norte (m)</td>
      <td style="text-align: center; font-weight: bold;">Azimute</td>
      <td style="text-align: center; font-weight: bold;">Dist&acirc;ncia (m)</td>
      <td style="text-align: center; font-weight: bold;">Longitude</td>
      <td style="text-align: center; font-weight: bold;">Latitude</td>
    </tr>
    '''
        
        linha = '''<tr>
      <td>[EST1]</td>
      <td>[EST2]</td>
      <td>[E]</td>
      <td>[N]</td>
      <td>[AZ]</td>
      <td>[D]</td>
      <td>[LON]</td>
      <td>[LAT]</td>
    </tr>
  '''
        
        FIM = '''</tbody>
</table>
<br>
<span style="font-weight: bold;">Per&iacute;metro:</span>
&nbsp;[PERIMETRO] m<br>
<span style="font-weight: bold;">&Aacute;rea Total:</span>
[AREA] m&sup2; / [AREA_HA] ha
</body>
</html>
'''
        
        # Inserindo dados iniciais do levantamento
        itens = {'[IMOVEL]': self.str2HTML(feat1['imóvel']),
                    '[UF]': feat1['UF'],
                    '[AREA]': '{:,.2f}'.format(feat1['area']).replace(',', 'X').replace('.', ',').replace('X', '.'),
                    '[UTM]': (SRC.split('/')[-1]).replace('zone', 'fuso'),
                    '[MUNICIPIO]': self.str2HTML(feat1['município']),
                    '[PERIMETRO]': '{:,.2f}'.format(feat1['perimetro']).replace(',', 'X').replace('.', ',').replace('X', '.')
                    }
        for item in itens:
                INICIO = INICIO.replace(item, itens[item])
                
        # Inserindo dados finais do levantamento
        itens = {   '[AREA]': '{:,.2f}'.format(feat1['area']).replace(',', 'X').replace('.', ',').replace('X', '.'),
                    '[AREA_HA]': '{:,.2f}'.format(feat1['area']/1e4).replace(',', 'X').replace('.', ',').replace('X', '.'),
                    '[PERIMETRO]': '{:,.2f}'.format(feat1['perimetro']).replace(',', 'X').replace('.', ',').replace('X', '.')
                    }
        for item in itens:
                FIM = FIM.replace(item, itens[item])
        
        LINHAS = INICIO
        
        pnts_UTM = {}
        for feat in vertices.getFeatures():
            pnt = feat.geometry().asMultiPoint()[0]
            pnts_UTM[feat['ordem']] = [coordinateTransformer.transform(pnt), feat['codigo'], pnt]

        # Cálculo dos Azimutes e Distâncias
        tam = len(pnts_UTM)
        feedback.pushInfo(str(tam))
        Az_lista, Dist = [], []
        for k in range(tam):
            pntA = pnts_UTM[k+1][0]
            pntB = pnts_UTM[1 if k+2 > tam else k+2][0]
            Az_lista += [(180/pi)*self.azimute(pntA, pntB)[0]]
            Dist += [sqrt((pntA.x() - pntB.x())**2 + (pntA.y() - pntB.y())**2)]

        for k in range(tam):
            linha0 = linha
            itens = {
                  '[EST1]': pnts_UTM[k+1][1],
                  '[EST2]': pnts_UTM[1 if k+2 > tam else k+2][1],
                  '[E]': '{:,.2f}'.format(pnts_UTM[k+1][0].x()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                  '[N]': '{:,.2f}'.format(pnts_UTM[k+1][0].y()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                  '[AZ]': self.str2HTML(self.dd2dms(Az_lista[k],1).replace('.', ',')),
                  '[D]': '{:,.2f}'.format(Dist[k]).replace(',', 'X').replace('.', ',').replace('X', '.'),
                  '[LON]': self.str2HTML(self.dd2dms(pnts_UTM[k+1][2].x(),4)),
                  '[LAT]': self.str2HTML(self.dd2dms(pnts_UTM[k+1][2].y(),4))
                        }
            for item in itens:
                linha0 = linha0.replace(item, itens[item])

            LINHAS += linha0
        
        LINHAS += FIM
        
        # Check for cancelation
        if feedback.isCanceled():
            return {}
        
        output = self.parameterAsFileOutput(parameters, self.HTML, context)
        arq = open(output, 'w')
        arq.write(LINHAS)
        arq.close()
        
        feedback.pushInfo(self.tr('Operation completed successfully!'))
        feedback.pushInfo('Leandro França - Eng Cart')
        
        return {self.HTML: output}