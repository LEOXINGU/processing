# -*- coding: utf-8 -*-

"""
closedPolygonal.py
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
__copyright__ = '(C) 2019, Leandro França'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import *
import processing
from numpy import sin, cos, modf, radians, sqrt, floor


class ClosedPolygonal(QgsProcessingAlgorithm):

    TABLE = 'TABLE'
    E_0 = 'E_0'
    N_0 = 'N_0'
    AZIMUTH_0 = 'AZIMUTH_0'
    STATION = 'STATION'
    FWD = 'FWD'
    ANGLE = 'ANGLE'
    DISTANCE = 'DISTANCE'
    POINTS = 'POINTS'
    CRS = 'CRS'
    HTML = 'HTML'
    

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ClosedPolygonal()

    def name(self):
        return 'planimetry'

    def displayName(self):
        return self.tr('Closed Polygonal')

    def group(self):
        return self.tr('LF Surveyor')

    def groupId(self):
        return 'lf_surveyor'

    def shortHelpString(self):
        return self.tr("Calculates the adjusted coordinates from angles and horizontal distances of a Closed Polygonal")

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
            QgsProcessingParameterNumber(
                self.E_0,
                self.tr('E (origin)'),
                type = 1, # float = 1 and integer = 0
                defaultValue = 1000.0
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.N_0,
                self.tr('N (origin)'),
                type = 1,
                defaultValue = 1000.0
            )
        )
        
        self.addParameter(
            QgsProcessingParameterString(
                self.AZIMUTH_0,
                self.tr('Azimuth (origin)'),
                defaultValue = '''0°00'00.0"'''
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.STATION,
                self.tr('Station'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.Numeric
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.FWD,
                self.tr('Forward'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.Numeric
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.ANGLE,
                self.tr('Angle'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.String
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.DISTANCE,
                self.tr('Distance'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.Numeric
            )
        )
        
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS, 
                self.tr('Coordinates Reference System'), 
                'ProjectCrs'
            )
        )
        
        # OUTPUT
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.POINTS,
                self.tr('Adjusted Points')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFileDestination(
                'HTML',
                self.tr('Adjustment Report'),
                self.tr('HTML files (*.html)')
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
        
    def dms2dd(self, txt):
        txt = txt.replace(' ','').replace(',','.')
        newtxt =''
        for letter in txt:
            if not letter.isnumeric() and letter != '.' and letter != '-':
                newtxt += '|'
            else:
                newtxt += letter
        lista = newtxt[:-1].split('|')
        if len(lista) != 3: # GMS
            return None
        else:
            if '-' in lista[0]: 
                return -1*(abs(float(lista[0])) + float(lista[1])/60 + float(lista[2])/3600)
            else:
                return float(lista[0]) + float(lista[1])/60 + float(lista[2])/3600

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
    
    def str2HTML(self, texto):
        if texto:
            dicHTML = {'Á': '&Aacute;',	'á': '&aacute;',	'Â': '&Acirc;',	'â': '&acirc;',	'À': '&Agrave;',	'à': '&agrave;',	'Å': '&Aring;',	'å': '&aring;',	'Ã': '&Atilde;',	'ã': '&atilde;',	'Ä': '&Auml;',	'ä': '&auml;',	'Æ': '&AElig;',	'æ': '&aelig;',	'É': '&Eacute;',	'é': '&eacute;',	'Ê': '&Ecirc;',	'ê': '&ecirc;',	'È': '&Egrave;',	'è': '&egrave;',	'Ë': '&Euml;',	'ë': '&Euml;',	'Ð': '&ETH;',	'ð': '&eth;',	'Í': '&Iacute;',	'í': '&iacute;',	'Î': '&Icirc;',	'î': '&icirc;',	'Ì': '&Igrave;',	'ì': '&igrave;',	'Ï': '&Iuml;',	'ï': '&iuml;',	'Ó': '&Oacute;',	'ó': '&oacute;',	'Ô': '&Ocirc;',	'ô': '&ocirc;',	'Ò': '&Ograve;',	'ò': '&ograve;',	'Ø': '&Oslash;',	'ø': '&oslash;',	'Ù': '&Ugrave;',	'ù': '&ugrave;',	'Ü': '&Uuml;',	'ü': '&uuml;',	'Ç': '&Ccedil;',	'ç': '&ccedil;',	'Ñ': '&Ntilde;',	'ñ': '&ntilde;',	'Ý': '&Yacute;',	'ý': '&yacute;',	'"': '&quot;', '”': '&quot;',	'<': '&lt;',	'>': '&gt;',	'®': '&reg;',	'©': '&copy;',	'\'': '&apos;', 'ª': '&ordf;', 'º': '&ordm', '°':'&deg;'}
            for item in dicHTML:
                if item in texto:
                    texto = texto.replace(item, dicHTML[item])
            return texto
        else:
            return ''
    
    def processAlgorithm(self, parameters, context, feedback):

        table = self.parameterAsSource(
            parameters,
            self.TABLE,
            context
        )
        
        if table is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.TABLE))
            
        E_0 = self.parameterAsDouble(
            parameters,
            self.E_0,
            context
        )
        
        N_0 = self.parameterAsDouble(
            parameters,
            self.N_0,
            context
        )
        
        Az_0 = self.parameterAsString(
            parameters,
            self.AZIMUTH_0,
            context
        )
        
        stations = self.parameterAsFields(
            parameters,
            self.STATION,
            context
        )
        
        fwds = self.parameterAsFields(
            parameters,
            self.FWD,
            context
        )
        
        angles = self.parameterAsFields(
            parameters,
            self.ANGLE,
            context
        )
        
        distances = self.parameterAsFields(
            parameters,
            self.DISTANCE,
            context
        )
        
        #feedback.pushInfo('Fields: {}, {}, {}, {}.'.format(stations[0], fwds[0], angles[0], distances[0]))
        
        html_output = self.parameterAsFileOutput(
            parameters, 
            self.HTML, 
            context
        )
        
        CRS = self.parameterAsCrs(
            parameters,
            self.CRS,
            context
        )
        
        # Field index
        station_id = table.fields().indexFromName(stations[0])
        #back_id = table.fields().indexFromName('Pto_Ré')
        fwd_id = table.fields().indexFromName(fwds[0])
        angle_id = table.fields().indexFromName(angles[0])
        dist_id = table.fields().indexFromName(distances[0])
        
        readings = {}
        SomaAng = 0
        
        for feat in table.getFeatures():
            att = feat.attributes()
            SomaAng += self.dms2dd(att[angle_id])
            readings[att[station_id]] = {'fwd':att[fwd_id] , 'angle': self.dms2dd(att[angle_id]) , 'dist':att[dist_id]}
        
        n = len(readings)
        # Erro de Fechamento Angular (ângulos internos - sentido anti-horário)
        E_alfa = SomaAng - (n-2)*180
        
        # Compensação do Erro de Fechamento Angular
        C_alfa = - E_alfa/n
        SomaAng_Comp = 0
        for est in readings:
            readings[est]['angle_comp'] = readings[est]['angle'] + C_alfa
            SomaAng_Comp += readings[est]['angle'] + C_alfa
        
        # Cálculo dos Azimutes e Deltas
        Az_0 = self.dms2dd(Az_0)
        Az = Az_0
        soma_delta_x = 0
        soma_delta_y = 0
        perimetro = 0
        for est in readings:
            if est !=1:
                Az = readings[est]['angle_comp'] + Az + 180
            readings[est]['Az'] = Az%360
            delta_x = readings[est]['dist']*cos(radians(90-Az))
            delta_y = readings[est]['dist']*sin(radians(90-Az))
            readings[est]['delta_x'] = delta_x
            readings[est]['delta_y'] = delta_y
            soma_delta_x += delta_x
            soma_delta_y += delta_y
            perimetro += readings[est]['dist']
        
        E_linear = sqrt(soma_delta_x**2 + soma_delta_y**2)
        Precisao = '1/'+ str(round(perimetro/E_linear,4))
        
        soma_delta_x, soma_delta_y = 0,0 ################################## APAGAR
        # Compensação Linear
        for est in readings:
            readings[est]['delta_x_comp'] = readings[est]['delta_x'] - soma_delta_x*readings[est]['dist']/perimetro
            readings[est]['delta_y_comp'] = readings[est]['delta_y'] - soma_delta_y*readings[est]['dist']/perimetro
        
        # Coordenadas Finais
        E = E_0
        N = N_0
        for est in readings:
            if est ==1:
                readings[est]['E'] = E
                readings[est]['N'] = N
            else:
                readings[est]['E'] = readings[est-1]['E'] + readings[est-1]['delta_x_comp']
                readings[est]['N'] = readings[est-1]['N'] + readings[est-1]['delta_y_comp']
        
        # Relatório
        texto_inicial = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
  <title>Traditional</title>
</head>
<body>
<p style="line-height: 107%;" align="center"><font
 style="font-size: 12pt;" size="3"><b>ADJUSTMENT
BY TRADITIONAL METHOD</b></font></p>
<p align="center">&nbsp;</p>
<p align="center"><u>ANALYTICAL CALCULATION
TOPOGRAPHY</u></p>
<table cellpadding="2" cellspacing="0" width="1204">
  <colgroup><col width="96"></colgroup> <colgroup><col
 width="96"><col width="96"><col width="96"><col
 width="96"><col width="96"><col width="96"><col
 width="96"><col width="96"><col width="96"><col
 width="96"><col width="96"></colgroup> <tbody>
    <tr valign="top">
      <td style="border: 1pt solid rgb(0, 0, 0); padding: 0.05cm;"
 width="96">
      <p align="center">Station</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">Forward</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">Angle</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">Distance</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">Corrected Angle</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">Azimuth</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">dE</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">dN</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">Corrected&nbsp;</p>
      <p align="center">dE</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">Corrected&nbsp;</p>
      <p align="center">dN</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">Final E</p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: rgb(0, 0, 0) rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0.05cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">Final N</p>
      </td>
    </tr>'''
        texto_tabela ='''    <tr valign="top">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0); border-width: medium 1pt 1pt; padding: 0cm 0.05cm 0.05cm;"
 width="96">
      <p align="center">[Sn]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[fSn]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[An]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[d]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[cA]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[Az]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[dE]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[dN]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[cdE]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[cdN]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[fE]</p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color rgb(0, 0, 0) rgb(0, 0, 0) -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 0.05cm 0.05cm 0cm;"
 width="96">
      <p align="center">[fN]</p>
      </td>
    </tr>'''
        texto_final ='''    <tr valign="top">
      <td colspan="2"
 style="border: medium none ; padding: 0cm;" width="197">
      <p style="text-align: right;">Sum:</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">[SumAn]&nbsp;</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">&nbsp;[SumD]</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">[SumCAng]&nbsp;</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">&nbsp;</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">&nbsp;[SumdE]</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">&nbsp;[SumdN]</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">[SumCdE]&nbsp;</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">&nbsp;[SumCdN]&nbsp;</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">&nbsp;</p>
      </td>
      <td style="border: medium none ; padding: 0cm;"
 width="96">
      <p align="center">&nbsp;</p>
      </td>
    </tr>
  </tbody>
</table>
<p align="center">&nbsp;</p>
<p lang="en-US">Angular closure error: [Ace]</p>
<p lang="en-US">Linear closure error: [Lce]</p>
<p lang="en-US">Linear relative error: [Lre]</p>
<p>&nbsp;</p>
<p>&nbsp;</p>
<p align="center" lang="en-US">_________________________________________</p>
<p align="center" lang="en-US">LEANDRO
FRAN&Ccedil;A</p>
<p align="center" lang="en-US">Cartographic Engineer</p>
<p>&nbsp;</p>
<p><a href="mailto:geoleandro.franca@gmail.com"><span
 lang="en-US">geoleandro.franca@gmail.com</span></a></p>
<p><a href="https://www.facebook.com/GEOCAPT/"><span
 lang="en-US">https://www.facebook.com/GEOCAPT/</span></a></p>
<p>&nbsp;</p>
<p style="margin-bottom: 0cm; line-height: 100%;"><br>
</p>
</body>
</html>
'''

        texto = texto_inicial

        # Alimentando tabela
        for est in readings:
            tableRowN = texto_tabela
            itens  = {
                         '[Sn]' : str(est),
                         '[fSn]': str(readings[est]['fwd']),
                         '[An]': self.str2HTML(self.dd2dms(readings[est]['angle'],1)),
                         '[d]': str(round(readings[est]['dist'],4)),
                         '[cA]': self.str2HTML(self.dd2dms(readings[est]['angle_comp'],1)),
                         '[Az]': self.str2HTML(self.dd2dms(readings[est]['Az'],1)),
                         '[dE]': str(round(readings[est]['delta_x'],4)),
                         '[dN]': str(round(readings[est]['delta_y'],4)),
                         '[cdE]': str(round(readings[est]['delta_x_comp'],4)),
                         '[cdN]': str(round(readings[est]['delta_y_comp'],4)),
                         '[fE]': str(round(readings[est]['E'],4)),
                         '[fN]': str(round(readings[est]['N'],4))
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            texto += tableRowN

        # Dados finais
        itens  = {
                     '[SumAn]' : self.str2HTML(self.dd2dms(SomaAng,1)),
                     '[SumD]': str(perimetro),
                     '[SumCAng]': self.str2HTML(self.dd2dms(SomaAng_Comp,1)),
                     '[SumdE]': str(round(soma_delta_x,4)),
                     '[SumdN]': str(round(soma_delta_y,4)),
                     '[SumCdE]': str(0),
                     '[SumCdN]': str(0),
                     '[Ace]': self.str2HTML(self.dd2dms(E_alfa,2)),
                     '[Lce]': str(round(E_linear,4)),
                     '[Lre]': Precisao
                     }
        for item in itens:
                texto_final = texto_final.replace(item, itens[item])

        texto += texto_final

        # Exportar HTML
        arq = open(html_output, 'w')
        arq.write(texto)
        arq.close()

        # Camada de Saída
        GeomType = QgsWkbTypes.Point
        Fields = QgsFields()
        itens  = {
                     'estation' : QVariant.Int,
                     'forward':  QVariant.Int,
                     'angle': QVariant.String,
                     'distance':  QVariant.Double,
                     'corrAng': QVariant.String,
                     'azimuth': QVariant.String,
                     'deltaE': QVariant.Double,
                     'deltaN': QVariant.Double,
                     'CdeltaE': QVariant.Double,
                     'CdeltaN': QVariant.Double,
                     'E': QVariant.Double,
                     'N': QVariant.Double,
                     }
        for item in itens:
            Fields.append(QgsField(item, itens[item]))
        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.POINTS,
            context,
            Fields,
            GeomType,
            CRS
        )
        
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.POINTS))
        
        # Criar pontos ajustados
        feat = QgsFeature(Fields)
        for est in readings:
            itens  = {
                         'estation' : str(est),
                         'forward': str(readings[est]['fwd']),
                         'angle': self.dd2dms(readings[est]['angle'],1),
                         'distance': str(round(readings[est]['dist'],4)),
                         'corrAng': self.dd2dms(readings[est]['angle_comp'],1),
                         'azimuth': self.dd2dms(readings[est]['Az'],1),
                         'deltaE': str(round(readings[est]['delta_x'],4)),
                         'deltaN': str(round(readings[est]['delta_y'],4)),
                         'CdeltaE': str(round(readings[est]['delta_x_comp'],4)),
                         'CdeltaN': str(round(readings[est]['delta_y_comp'],4)),
                         'E': str(round(readings[est]['E'],4)),
                         'N': str(round(readings[est]['N'],4))
                         }
            for item in itens:
                feat[item] = itens[item]
            geom = QgsGeometry.fromPointXY(QgsPointXY(readings[est]['E'], readings[est]['N']))
            feat.setGeometry(geom)
            sink.addFeature(feat, QgsFeatureSink.FastInsert)
            if feedback.isCanceled():
                break
        
        feedback.pushInfo(self.tr('Operation completed successfully!'))
        feedback.pushInfo('Leandro França - Eng Cart')
        
        return {self.POINTS: dest_id,
                    self.HTML: html_output}
