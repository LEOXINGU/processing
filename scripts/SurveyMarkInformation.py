# -*- coding: utf-8 -*-

"""
***************************************************************************
    SurveyMarkInformation.py
    ---------------------
    Date                 : Jul 10
    Copyright            : (C) 2020 by Leandro França
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
__date__ = 'Jul 10'
__copyright__ = '(C) 2020, Leandro França'

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsFeatureRequest,
                       QgsExpression,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFileDestination,
                       QgsApplication,
                       QgsProject,
                       QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem)
from math import atan, pi, sqrt, floor
import math, os, base64, PIL.Image

class SurveyMarkDoc(QgsProcessingAlgorithm):

    PONTOREF = 'PONTOREF'
    AREAIMOVEL = 'AREAIMOVEL'
    CODIGO = 'CODIGO'
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
        return SurveyMarkDoc()

    def name(self):
        return 'surveymarkdoc'

    def displayName(self):
        return self.tr('Survey Mark Informations', 'Monografia de Marcos')

    def group(self):
        return self.tr('LF Documents', 'LF Documentos')

    def groupId(self):
        return 'lf_documents'

    def shortHelpString(self):
        return self.tr('This tool generates monograph(s) of geodetic landmarks automatically from the "pto_ref_geod_topo_p" layer.', 'Esta ferramenta gera monografia(s) de marcos geodésicos de forma automática a partir da camada "pto_ref_geod_topo_p".')

    def initAlgorithm(self, config=None):
        
        # 'INPUTS'
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PONTOREF,
                self.tr('Survey Landmark', 'Marco Geodésico'),
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
        
        self.addParameter(
            QgsProcessingParameterString(
                self.CODIGO,
                self.tr('Code', 'Código')
            )
        )
            
        # 'OUTPUTS'
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.HTML,
                self.tr('Geodetic Landmark Monograph', 'Monografia de Marco Geodésico'),
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
    
    # Imagem para HTML
    def img2html(self, path_file):
        arq = open(path_file, 'rb')
        leitura = arq.read()
        arq.close()
        encoded = base64.b64encode(leitura)
        texto = str(encoded)[2:-1]
        return texto
    
    # Redimensionar Imagem
    def ImgResize(self, path_file, lado, resized):
        caminho, arquivo = os.path.split(path_file)
        img = PIL.Image.open(path_file)
        altura = img.size[1]
        largura = img.size[0]
        if largura < altura:
            new_height = lado
            new_width =int(lado/float(altura)*largura)
        else:
            new_width = lado
            new_height =int(lado/float(largura)*altura)
            
        img = img.resize((new_width, new_height))
        path_file_reduced = os.path.join(caminho, resized)
        img.save(path_file_reduced)
        del img
        return path_file_reduced
        
    # Imagem para HTML redimensionada
    def img2html_resized(self, path_file, lado=500, resized = 'reduzido.jpg'):
        if os.path.isfile(path_file):
            caminho, arquivo = os.path.split(path_file)
            path_file_reduced = self.ImgResize(path_file, lado, resized)
            texto = self.img2html(path_file_reduced)
            os.remove(path_file_reduced)
            return texto
        else:
            return ''
    
    # Meridiano Central
    def MC(self, pnt):
        lon = pnt.x()
        lat = pnt.y()
        # Calculo do Fuso
        fuso = round((183+lon)/6.0)
        # MC
        MC = 6*fuso - 183
        return MC

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
        
        vertice = self.parameterAsSource(parameters,
                                                     self.PONTOREF,
                                                     context)
        area = self.parameterAsSource(parameters,
                                                     self.AREAIMOVEL,
                                                     context)
        codigo = self.parameterAsString(parameters,
                                                     self.CODIGO,
                                                     context)
        
        if vertice is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.PONTOREF))
        if area is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.AREAIMOVEL))
        if codigo is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.CODIGO))
        
        
        
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
                area = feat
                break
        
        expr = QgsExpression( "\"codigo\"='{}'".format( codigo ) )
        pnt = False
        for feat in vertice.getFeatures(QgsFeatureRequest( expr )):
            pnt = feat.geometry().asMultiPoint()[0]
            ponto = feat
            break
                
        pnts_UTM = coordinateTransformer.transform(pnt)
        
        TEXTO = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">
  <title>Monografia de Marco Geod&eacute;sico</title>
</head>
<body>
<div style="text-align: center;"><span style="font-weight: bold;"><br>
<img src="data:image/jpg;base64,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"><br>
MINIST&Eacute;RIO DA DEFESA</span><br style="font-weight: bold;">
<span style="font-weight: bold;">EX&Eacute;RCITO BRASILEIRO</span><br style="font-weight: bold;">
<span style="font-weight: bold;">DEPARTAMENTO DE CI&Ecirc;NCIA E TECNOLOGIA</span><br style="font-weight: bold;">
<span style="font-weight: bold;">3&ordm; CENTRO DE GEOINFORMA&Ccedil;&Atilde;O</span><br>
<br>
<table style="text-align: left; width: 100%;" border="1" cellpadding="1" cellspacing="0">
  <tbody>
    <tr style="font-weight: bold;" align="center">
      <td colspan="5" rowspan="1">MONOGRAFIA DE MARCO GEOD&Eacute;SICO</td>
    </tr>
    <tr>
      <td style="text-align: center; font-weight: bold;">C&Oacute;DIGO</td>
      <td style="text-align: center; font-weight: bold;">TIPO</td>
      <td style="text-align: center; font-weight: bold;">NOME DO IM&Oacute;VEL</td>
      <td style="text-align: center; font-weight: bold;">MUNIC&Iacute;PIO</td>
      <td style="text-align: center; font-weight: bold;">UF</td>
    </tr>
    <tr>
      <td style="text-align: center;">[CD]</td>
      <td style="text-align: center;">[TP]</td>
      <td style="text-align: center;">[NI]</td>
      <td style="text-align: center;">[MUN]</td>
      <td style="text-align: center;">[UF]</td>
    </tr>
    <tr>
      <td colspan="5" rowspan="1">Descri&ccedil;&atilde;o/Localiza&ccedil;&atilde;o: [DESCR]</td>
    </tr>
    <tr>
      <td colspan="5" rowspan="1"></td>
    </tr>
    <tr>
      <td style="text-align: center; font-weight: bold;" colspan="2" rowspan="1">COORDENADAS GEOD&Eacute;SICAS</td>
      <td style="text-align: center; font-weight: bold;" colspan="2" rowspan="1">COORDENADAS PLANAS (UTM)</td>
      <td style="text-align: center; font-weight: bold;">PRECIS&Otilde;ES (m)</td>
    </tr>
    <tr>
      <td>Longitude <span style="font-family: &quot;Times New Roman&quot;,serif;">(</span><big><big><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;">&lambda;</span></big></big><span style="font-family: &quot;Times New Roman&quot;,serif;">)</span></td>
      <td>[LON]</td>
      <td>Este</td>
      <td>[E] m</td>
      <td><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;"></span><big><big><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;"></span></big></big><span style="font-family: &quot;Times New Roman&quot;,serif;">&sigma;(</span><big><big><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;">&lambda;</span></big></big><span style="font-family: &quot;Times New Roman&quot;,serif;">) &nbsp;= &nbsp;[sigma_x]</span><b><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;"></span></b><b><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;"></span></b></td>
    </tr>
    <tr>
      <td>Latitude <span style="font-family: &quot;Times New Roman&quot;,serif;">(&phi;)</span></td>
      <td>[LAT]</td>
      <td>Norte</td>
      <td>[N] m</td>
      <td><b><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;"></span></b><b><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;"></span></b><b><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;"></span></b><span style="font-family: &quot;Times New Roman&quot;,serif;">&sigma;(&phi;) = </span><span style="font-family: &quot;Times New Roman&quot;,serif;">[sigma_y]</span></td>
    </tr>
    <tr>
      <td>Altitude Elipsoidal (h)</td>
      <td>[h] m</td>
      <td>MC</td>
      <td>[MC]</td>
      <td><b><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;"></span></b><b><span style="font-size: 9pt; font-family: &quot;Times New Roman&quot;,serif;"></span></b>&sigma;(h) = <span style="font-family: &quot;Times New Roman&quot;,serif;">[sigma_h]</span></td>
    </tr>
    <tr>
      <td>Altitude Ortom&eacute;trica (H)</td>
      <td>[H] m</td>
      <td></td>
      <td></td>
      <td></td>
    </tr>
    <tr>
      <td colspan="5" rowspan="1"></td>
    </tr>
    <tr>
      <td style="font-weight: bold;">EQUIPAMENTO:</td>
      <td>[EQP]</td>
      <td style="font-weight: bold; text-align: center;">ETAPA</td>
      <td style="font-weight: bold; text-align: center;">DATA</td>
      <td style="font-weight: bold; text-align: center;">RESPONS&Aacute;VEL</td>
    </tr>
    <tr>
      <td style="font-weight: bold;">M&Eacute;TODO:</td>
      <td>[MET]</td>
      <td>Levantamento</td>
      <td>[LEV_DT]</td>
      <td>[LEV_RESP]</td>
    </tr>
    <tr>
      <td style="font-weight: bold;">BASE(S) DE REF.:</td>
      <td>[BASE]</td>
      <td>Processamento</td>
      <td>[PROC_DT]</td>
      <td>[PROC_RESP]</td>
    </tr>
    <tr>
      <td><span style="font-weight: bold;">SOFTWARE:</span></td>
      <td>[SOFT]</td>
      <td>Monografia</td>
      <td>[MON_DT]</td>
      <td>[MON_RESP]</td>
    </tr>
    <tr>
      <td colspan="5" rowspan="1"></td>
    </tr>
    <tr>
      <td style="text-align: center;" colspan="2" rowspan="1"><span style="font-weight: bold;">FOTO DO MARCO</span></td>
      <td style="text-align: center;" colspan="3" rowspan="1"><span style="font-weight: bold;">IMAGEM A&Eacute;REA</span></td>
    </tr>
    <tr>
      <td style="text-align: center;" colspan="2" rowspan="1"><img style="width: 200px; height: 150px;" alt="marco" src="data:image/jpg;base64,[FOTO_MARCO]"></td>
      <td style="text-align: center;" colspan="3" rowspan="3"><img style="width: 300px; height: 400px;" alt="imagem" src="data:image/jpg;base64,[IMAGEM_AER]"></td>
    </tr>
    <tr style="font-weight: bold;">
      <td style="text-align: center;" colspan="2" rowspan="1">FOTO PANOR&Acirc;MICA</td>
    </tr>
    <tr align="center">
      <td colspan="2" rowspan="1"><img style="width: 200px; height: 150px;" alt="panoramica" src="data:image/jpg;base64,[FOTO_PAN]"></td>
    </tr>
    <tr>
      <td colspan="5" rowspan="1">Obs.: [OBS]</td>
    </tr>
    <tr>
      <td colspan="5" rowspan="1"></td>
    </tr>
    <tr>
      <td style="text-align: center; font-weight: bold;" colspan="3" rowspan="1">RESPONS&Aacute;VEL T&Eacute;CNICO</td>
      <td style="text-align: center; font-weight: bold;">CONFEA/CREA</td>
      <td style="text-align: center; font-weight: bold;">C&Oacute;D. CRED. INCRA</td>
    </tr>
    <tr>
      <td style="text-align: center;" colspan="3" rowspan="1">[REP_TEC]</td>
      <td style="text-align: center;">[CREA]</td>
      <td style="text-align: center;">[COD_INCRA]</td>
    </tr>
  </tbody>
</table>
</div>
</body>
</html>'''

        tipos = {1: 'Atimétrico',
                 2: 'Planimétrico',
                 3: 'Planialtimétrico',
                 4: 'Gravimétrico'}
        metodo = {1: 'PPP', 2: 'Relativo Estático'}
    
    
        # Inserindo dados iniciais do levantamento
        itens = {'[CD]': self.str2HTML(ponto['codigo']),
                '[TP]':  self.str2HTML(tipos[ponto['tipoptorefgeodtopo']]) ,
                '[NI]':  self.str2HTML(area['imóvel']),
                '[MUN]': self.str2HTML(area['município']),
                '[UF]':  self.str2HTML(area['UF']),
                '[LON]': self.str2HTML(self.dd2dms(pnt.x(),4)),
                '[LAT]': self.str2HTML(self.dd2dms(pnt.y(),4)),
                '[h]': '{:,.3f}'.format(ponto['altitude']).replace(',', 'X').replace('.', ',').replace('X', '.'),
                '[H]': '{:,.3f}'.format(ponto['altitudeortometrica']).replace(',', 'X').replace('.', ',').replace('X', '.'),
                '[E]': '{:,.3f}'.format(pnts_UTM.x()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                '[N]': '{:,.3f}'.format(pnts_UTM.y()).replace(',', 'X').replace('.', ',').replace('X', '.'),
                '[MC]':  str(self.MC(pnt)),
                '[sigma_x]': '{:,.3f}'.format(ponto['sigma_x']).replace(',', 'X').replace('.', ',').replace('X', '.'),
                '[sigma_y]': '{:,.3f}'.format(ponto['sigma_y']).replace(',', 'X').replace('.', ',').replace('X', '.'),
                '[sigma_h]': '{:,.3f}'.format(ponto['sigma_h']).replace(',', 'X').replace('.', ',').replace('X', '.'),
                '[EQP]':  self.str2HTML(ponto['equipamento']),
                '[MET]':  self.str2HTML(metodo[ponto['lev_metodo']]),
                '[BASE]':  self.str2HTML(ponto['lev_base_ref']),
                '[SOFT]':  self.str2HTML(ponto['software']),
                '[LEV_DT]': self.str2HTML(((ponto['lev_data']).toPyDate()).strftime("%d/%m/%Y")),
                '[LEV_RESP]': self.str2HTML(ponto['lev_resp']),
                '[PROC_DT]': self.str2HTML(((ponto['proc_data']).toPyDate()).strftime("%d/%m/%Y")),
                '[PROC_RESP]': self.str2HTML(ponto['proc_resp']),
                '[MON_DT]': self.str2HTML(((ponto['monografia_data']).toPyDate()).strftime("%d/%m/%Y")),
                '[MON_RESP]': self.str2HTML(ponto['monografia_resp']),
                '[REP_TEC]':  self.str2HTML(area['Resp_Tecnico']),
                '[CREA]': self.str2HTML(area['CREA']),
                '[COD_INCRA]': self.str2HTML(ponto['codigo_credenciado']),
                '[DESCR]': self.str2HTML(ponto['descricao']),
                '[FOTO_MARCO]': self.img2html_resized(ponto['foto_marco']) if ponto['foto_marco'] else '',
                '[FOTO_PAN]': self.img2html_resized(ponto['foto_panoramica']) if ponto['foto_panoramica'] else '',
                '[IMAGEM_AER]': self.img2html_resized(ponto['imagem_aerea']) if ponto['imagem_aerea'] else '',
                '[OBS]': self.str2HTML(ponto['obs'])
                    }
        for item in itens:
                TEXTO = TEXTO.replace(item, itens[item])
        
        
        # Check for cancelation
        if feedback.isCanceled():
            return {}
        
        output = self.parameterAsFileOutput(parameters, self.HTML, context)
        arq = open(output, 'w')
        arq.write(TEXTO)
        arq.close()
        
        feedback.pushInfo(self.tr('Operation completed successfully!', 'Operação finalizada com sucesso!'))
        feedback.pushInfo('Leandro França - Eng Cart')
        
        return {self.HTML: output}