# -*- coding: utf-8 -*-

"""
***************************************************************************
    memorial_descritivo.py
    ---------------------
    Date                 : Sept 22
    Copyright            : (C) 2019 by Leandro França
    Email                : geoleandro.franca@gmail.com
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
__date__ = 'Sept 22'
__copyright__ = '(C) 2019, Leandro França'

from qgis.core import (QgsProcessing,
                       QgsProject,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingException,
                       QgsProcessingParameterFileDestination)
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from math import atan, pi, sqrt
import math

class MemorialDescritivo(QgisAlgorithm):
    """
    This algorithm takes three vector layers (point, line, and polygon) 
    that define a specific ownership and creates an HTML file with the
    descriptive characteristics of the area.
    """
    HTML = 'HTML'
    INPUT1 = 'INPUT1'
    INPUT2 = 'INPUT2'
    INPUT3 = 'INPUT3'
    
    texto_inicial = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
  <title>descritivo</title>
</head>
<body>
<p class="western"
 style="margin-bottom: 0.0001pt; text-align: center;"
 align="center"><b><span style="font-size: 12pt;">MEMORIAL
DESCRITIVO</span></b><o:p></o:p></p>
<p class="western" style="margin-bottom: 0.0001pt;"><o:p>&nbsp;</o:p></p>
<table class="MsoTableGrid"
 style="border: medium none ; border-collapse: collapse;"
 border="0" cellpadding="0" cellspacing="0">
  <tbody>
    <tr style="">
      <td style="padding: 0cm 5.4pt; width: 247.85pt;"
 valign="top" width="330">
      <p class="western" style="margin-bottom: 0.0001pt;"><b>Im&oacute;vel:
</b>[IMOVEL]<o:p></o:p></p>
      </td>
      <td style="padding: 0cm 5.4pt; width: 176.85pt;"
 valign="top" width="236">
      <p class="western" style="margin-bottom: 0.0001pt;"><b>Comarca:</b>
[COMARCA]<o:p></o:p></p>
      </td>
    </tr>
    <tr style="">
      <td colspan="2"
 style="padding: 0cm 5.4pt; width: 424.7pt;" valign="top"
 width="566">
      <p class="western" style="margin-bottom: 0.0001pt;"><b>Propriet&aacute;rio:</b>
[PROPRIETARIO]<o:p></o:p></p>
      </td>
    </tr>
    <tr style="">
      <td style="padding: 0cm 5.4pt; width: 247.85pt;"
 valign="top" width="330">
      <p class="western" style="margin-bottom: 0.0001pt;"><b>UF:</b>
[UF]<b><o:p></o:p></b></p>
      </td>
      <td style="padding: 0cm 5.4pt; width: 176.85pt;"
 valign="top" width="236">
      <p class="western" style="margin-bottom: 0.0001pt;"><b>Munic&iacute;pio:
      </b>[MUNICIPIO]<o:p></o:p></p>
      </td>
    </tr>
    <tr style="">
      <td colspan="2"
 style="padding: 0cm 5.4pt; width: 424.7pt;" valign="top"
 width="566">
      <p class="western" style="margin-bottom: 0.0001pt;"><b>Matr&iacute;cula(s):</b>
[MATRICULAS]<o:p></o:p></p>
      </td>
    </tr>
    <tr style="">
      <td style="padding: 0cm 5.4pt; width: 247.85pt;"
 valign="top" width="330">
      <p class="western" style="margin-bottom: 0.0001pt;"><b>&Aacute;rea
(m<sup>2</sup>): </b>[AREA]<o:p></o:p></p>
      </td>
      <td style="padding: 0cm 5.4pt; width: 176.85pt;"
 valign="top" width="236">
      <p class="western" style="margin-bottom: 0.0001pt;"><b>Per&iacute;metro
(m):</b> [PERIMETRO]<o:p></o:p></p>
      </td>
    </tr>
    <tr style="">
      <td colspan="2"
 style="padding: 0cm 5.4pt; width: 424.7pt;" valign="top"
 width="566">
      <p class="western" style="margin-bottom: 0.0001pt;"><b>Sistema
de Refer&ecirc;ncia de Coordenadas:</b> [SRC]<b><o:p></o:p></b></p>
      </td>
    </tr>
  </tbody>
</table>
<p class="western" style="margin-bottom: 0.0001pt;"><o:p>&nbsp;</o:p></p>
<p class="western"
 style="margin-bottom: 0.0001pt; text-align: justify;">Inicia-se
a descri&ccedil;&atilde;o deste per&iacute;metro n'''

    texto_var1 = '''o
v&eacute;rtice <b>[Vn]</b>, de
coordenadas <b>N [Nn] m </b>e <b>E [En] m</b>,
[Descr_k], deste, segue
confrontando com [Confront_k], com os seguintes azimutes planos e
dist&acirc;ncias: [Az_n]
e [Dist_n] m at&eacute; '''

    texto_var2 = '''o v&eacute;rtice<span
 style="color: red;"> </span><b>[Vn]</b>,
de
coordenadas <b>N [Nn] m </b>e <b>E [En] m</b>;
[Az_n] e [Dist_n] m at&eacute; '''

    texto_final = '''o v&eacute;rtice <b>P-001</b>, de coordenadas <b>N
[N1] m </b>e <b>E [E1] m</b>, ponto
inicial da descri&ccedil;&atilde;o deste per&iacute;metro.
Todas as coordenadas aqui descritas est&atilde;o
georreferenciadas ao Sistema Geod&eacute;sico Brasileiro, tendo
como SGR o <b>SIRGAS2000</b>,
e encontram-se projetadas no Sistema UTM, fuso [FUSO] e
hemisf&eacute;rio [HEMISFERIO], a
partir das quais todos os azimutes e dist&acirc;ncias,
&aacute;rea e per&iacute;metro foram
calculados.<o:p></o:p></p>
<p class="western"
 style="margin-bottom: 0.0001pt; text-align: justify;"><o:p>&nbsp;</o:p></p>
<p class="western"
 style="margin-bottom: 0.0001pt; text-align: justify;"><o:p>&nbsp;</o:p></p>
<p class="western"
 style="margin-bottom: 0.0001pt; text-align: right;"
 align="right">Olinda - PE, [DATA].<o:p></o:p></p>
<p class="western" style="margin-bottom: 0.0001pt;"><o:p>&nbsp;</o:p></p>
<p class="western" style="margin-bottom: 0.0001pt;"><o:p>&nbsp;</o:p></p>
<p class="western"
 style="margin: 0cm 0cm 0.0001pt; text-align: center;"
 align="center">___________________________________________<o:p></o:p></p>
<p class="western"
 style="margin: 0cm 0cm 0.0001pt; text-align: center;"
 align="center">[RESP_TEC]<o:p></o:p></p>
<p class="western"
 style="margin: 0cm 0cm 0.0001pt; text-align: center;"
 align="center">[CREA]<o:p></o:p></p>
<p class="western"
 style="margin: 0cm 0cm 0.0001pt; text-align: center;"
 align="center">RESPONS&Aacute;VEL T&Eacute;CNICO<o:p></o:p></p>
<p class="MsoNormal"><o:p>&nbsp;</o:p></p>
</body>
</html>
'''

    def createInstance(self):
        # Must return a new copy of your algorithm.
        return MemorialDescritivo()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'memorialdescritivo'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Memorial Descritivo')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('LF Topografia')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs
        to.
        """
        return 'lf_topography'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Elaboração de Memorial Descritivo a partir de camadas vetorias que definem uma propriedade.')

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and outputs of the algorithm.
        """
        # 'INPUTS'
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT1',
                self.tr('Vertices'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT2',
                self.tr('Limits'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                'INPUT3',
                self.tr('Area'),
                types=[QgsProcessing.TypeVectorPolygon]
            )
        )
        # 'OUTPUTS'
        self.addParameter(
            QgsProcessingParameterFileDestination(
                'HTML',
                self.tr('Descriptive Memorial'),
                self.tr('HTML files (*.html)')
            )
        )
    
    # Acentos para HTML
    def str2HTML(self, texto):
        if texto:
            dicHTML = {'Á': '&Aacute;',	'á': '&aacute;',	'Â': '&Acirc;',	'â': '&acirc;',	'À': '&Agrave;',	'à': '&agrave;',	'Å': '&Aring;',	'å': '&aring;',	'Ã': '&Atilde;',	'ã': '&atilde;',	'Ä': '&Auml;',	'ä': '&auml;',	'Æ': '&AElig;',	'æ': '&aelig;',	'É': '&Eacute;',	'é': '&eacute;',	'Ê': '&Ecirc;',	'ê': '&ecirc;',	'È': '&Egrave;',	'è': '&egrave;',	'Ë': '&Euml;',	'ë': '&Euml;',	'Ð': '&ETH;',	'ð': '&eth;',	'Í': '&Iacute;',	'í': '&iacute;',	'Î': '&Icirc;',	'î': '&icirc;',	'Ì': '&Igrave;',	'ì': '&igrave;',	'Ï': '&Iuml;',	'ï': '&iuml;',	'Ó': '&Oacute;',	'ó': '&oacute;',	'Ô': '&Ocirc;',	'ô': '&ocirc;',	'Ò': '&Ograve;',	'ò': '&ograve;',	'Ø': '&Oslash;',	'ø': '&oslash;',	'Ù': '&Ugrave;',	'ù': '&ugrave;',	'Ü': '&Uuml;',	'ü': '&uuml;',	'Ç': '&Ccedil;',	'ç': '&ccedil;',	'Ñ': '&Ntilde;',	'ñ': '&ntilde;',	'Ý': '&Yacute;',	'ý': '&yacute;',	'"': '&quot;',	'<': '&lt;',	'>': '&gt;',	'®': '&reg;',	'©': '&copy;',	'\'': '&apos;', 'ª': '&ordf;', 'º': '&ordm'}
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
    def dd2dms(self, dd):
        is_positive = dd >= 0
        dd = abs(dd)
        minutes,seconds = divmod(dd*3600,60)
        degrees,minutes = divmod(minutes,60)
        degrees = str(int(degrees)) if is_positive else '-' + str(int(degrees))
        minutes = int(minutes)
        return degrees + "&deg;" + str(minutes).zfill(2) + "'" + ("{:.1f}".format(seconds)).zfill(4) + "''"

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        vertices = self.parameterAsSource(parameters,
                                                     'INPUT1',
                                                     context)
        limites = self.parameterAsSource(parameters,
                                                     'INPUT2',
                                                     context)
        area = self.parameterAsSource(parameters,
                                                     'INPUT3',
                                                     context)
                                                     
        meses = {1: 'janeiro', 2:'fevereiro', 3: 'março', 4:'abril', 5:'maio', 6:'junho', 7:'julho', 8:'agosto', 9:'setembro', 10:'outubro', 11:'novembro', 12:'dezembro'}

        # Pegando informações dos confrontantes (limites)
        ListaDescr = []
        ListaCont = []
        soma = 0
        for linha in limites.getFeatures():
            Lin_coord = linha.geometry().asMultiPolyline()[0]
            ListaDescr += [[self.str2HTML(linha['descr_pnt_inicial']), self.str2HTML(linha['confrontante'])]]
            cont = len(Lin_coord)
            ListaCont += [(soma, cont-1)]
            soma += cont-1

        # Pegando o SRC do Projeto
        SRC = QgsProject.instance().crs().description()

        # Dados do levantamento
        #Fields = area.fields()
        #fieldnames = [field.name() for field in Fields]
        for feat in area.getFeatures():
                feat1 = feat
                break

        geom = feat1.geometry()
        centroideG = geom.centroid().asPoint()

        # Transformar Coordenadas de Geográficas para o sistema UTM
        coordinateTransformer = QgsCoordinateTransform()
        coordinateTransformer.setDestinationCrs(QgsProject.instance().crs())
        coordinateTransformer.setSourceCrs(QgsCoordinateReferenceSystem('EPSG:4674'))

        pnts = {}

        for feat in vertices.getFeatures():
            pnts[feat['ordem']] = coordinateTransformer.transform(feat.geometry().asMultiPoint()[0])

        # Cálculo dos Azimutes e Distâncias
        tam = len(pnts)
        Az_lista, Dist = [], []
        for k in range(tam):
            pntA = pnts[k+1]
            pntB = pnts[max((k+2)%(tam+1),1)]
            Az_lista += [(180/pi)*self.azimute(pntA, pntB)[0]]
            Dist += [sqrt((pntA.x() - pntB.x())**2 + (pntA.y() - pntB.y())**2)]

        # Inserindo dados iniciais do levantamento
        itens = {'[IMOVEL]': self.str2HTML(feat1['imóvel']),
                    '[PROPRIETARIO]': self.str2HTML(feat1['proprietário']),
                    '[UF]': feat1['UF'],
                    '[MATRICULAS]': self.str2HTML(feat1['matrícula']),
                    '[AREA]': '{:,.2f}'.format(feat1['area']).replace(',', 'X').replace('.', ',').replace('X', '.'),
                    '[SRC]': SRC,
                    '[COMARCA]': self.str2HTML(feat1['município'] +' - ' + feat1['UF']),
                    '[MUNICIPIO]': self.str2HTML(feat1['município']),
                    '[PERIMETRO]': '{:,.2f}'.format(feat1['perimetro']).replace(',', 'X').replace('.', ',').replace('X', '.')
                    }

        for item in itens:
                self.texto_inicial = self.texto_inicial.replace(item, itens[item])

        LINHAS = self.texto_inicial
        for w,t in enumerate(ListaCont):
            linha0 = self.texto_var1
            itens = {'[Vn]': 'P-' + str(t[0]+1).zfill(3),
                        '[En]': '{:,.2f}'.format(pnts[t[0]+1].x()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                        '[Nn]': '{:,.2f}'.format(pnts[t[0]+1].y()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                        '[Az_n]': self.dd2dms(Az_lista[t[0]]).replace('.', ','),
                        '[Dist_n]': '{:,.2f}'.format(Dist[t[0]]).replace(',', 'X').replace('.', ',').replace('X', '.'),
                        '[Descr_k]': ListaDescr[w][0],
                        '[Confront_k]': ListaDescr[w][1]
                        }
            for item in itens:
                linha0 = linha0.replace(item, itens[item])
            LINHAS += linha0
            LIN0 = ''
            for k in range(t[0]+1, t[0]+t[1]):
                linha1 = self.texto_var2
                itens = {'[Vn]': 'P-' + str(k+1).zfill(3),
                        '[En]': '{:,.2f}'.format(pnts[k+1].x()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                        '[Nn]': '{:,.2f}'.format(pnts[k+1].y()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                        '[Az_n]': self.dd2dms(Az_lista[k]).replace('.', ','),
                        '[Dist_n]': '{:,.2f}'.format(Dist[k]).replace(',', 'X').replace('.', ',').replace('X', '.')
                        }
                for item in itens:
                    linha1 = linha1.replace(item, itens[item])
                LIN0 += linha1
            LINHAS += LIN0

        # Inserindo dados finais
        itens = {'[N1]': '{:,.2f}'.format(pnts[1].y()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                     '[E1]': '{:,.2f}'.format(pnts[1].x()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                     '[FUSO]': str(self.FusoHemisf(centroideG)[1]),
                     '[HEMISFERIO]': self.FusoHemisf(centroideG)[0],
                     '[RESP_TEC]': self.str2HTML(feat1['Resp_Tecnico']), 
                     '[CREA]': self.str2HTML(feat1['CREA']), 
                     '[LOCAL]': self.str2HTML((feat1['município']).title() +' - ' + (feat1['UF']).upper()),
                     '[DATA]': ((feat1['data_levantamento'].toPyDate()).strftime("%d de {} de %Y")).format(meses[feat1['data_levantamento'].month()])
                    }

        for item in itens:
                self.texto_final = self.texto_final.replace(item, itens[item])

        LINHAS += self.texto_final
        
        output = self.parameterAsFileOutput(parameters, self.HTML, context)
        arq = open(output, 'w')
        arq.write(LINHAS)
        arq.close()

        # Check for cancelation
        if feedback.isCanceled():
            return {}
        
        feedback.pushInfo(self.tr('Operation completed successfully!'))
        feedback.pushInfo('Leandro França - Eng Cart')
        #iface.messageBar().pushMessage("u'Situacao", "Operacao Concluida com Sucesso!", level=Qgis.Success, duration=5)
        
        return {self.HTML: output}
