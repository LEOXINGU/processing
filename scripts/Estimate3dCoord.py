# -*- coding: utf-8 -*-

"""
Estimate3dCoord.py
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
__date__ = '2020-02-07'
__copyright__ = '(C) 2020, Leandro França'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import *
import qgis.utils
from numpy import radians, array, sin, cos, sqrt, matrix, zeros, floor, identity, diag
from numpy.linalg import pinv, norm
import xlwt

class Estimate3dCoord(QgsProcessingAlgorithm):

    COC = 'COC'
    AZIMUTH = 'AZIMUTH'
    ZENITH = 'ZENITH'
    OUTPUT = 'OUTPUT'
    WEIGHT = 'WEIGHT'
    OPENOUTPUT = 'OPENOUTPUT'
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
        
        return Estimate3dCoord()

    def name(self):

        return 'estimate3dcoord'

    def displayName(self):

        return self.tr('Estimate 3D Coordinates', 'Estimar Coordenadas 3D')

    def group(self):

        return self.tr('LF Survey', 'LF Agrimensura')

    def groupId(self):

        return 'lf_survey'

    def shortHelpString(self):
        if self.LOC == 'pt':
            return "Esta ferramenta calcula as coordenadas (X,Y,Z) de um ponto a partir de medições de azimute e ângulo zenital observados de duas ou mais estações de coordenadas conhecidas utilizando o Método das Distâncias Mínimas."
        else:
            return self.tr("This tool calculates the coordinates (X, Y, Z) of a point from azimuth and zenith angle measurements observed from two or more stations with known coordinates using the Minimum Distances Method.")
        return self.tr()
            
    def str2HTML(self, texto):
        if texto:
            dicHTML = {'Á': '&Aacute;',	'á': '&aacute;',	'Â': '&Acirc;',	'â': '&acirc;',	'À': '&Agrave;',	'à': '&agrave;',	'Å': '&Aring;',	'å': '&aring;',	'Ã': '&Atilde;',	'ã': '&atilde;',	'Ä': '&Auml;',	'ä': '&auml;',	'Æ': '&AElig;',	'æ': '&aelig;',	'É': '&Eacute;',	'é': '&eacute;',	'Ê': '&Ecirc;',	'ê': '&ecirc;',	'È': '&Egrave;',	'è': '&egrave;',	'Ë': '&Euml;',	'ë': '&Euml;',	'Ð': '&ETH;',	'ð': '&eth;',	'Í': '&Iacute;',	'í': '&iacute;',	'Î': '&Icirc;',	'î': '&icirc;',	'Ì': '&Igrave;',	'ì': '&igrave;',	'Ï': '&Iuml;',	'ï': '&iuml;',	'Ó': '&Oacute;',	'ó': '&oacute;',	'Ô': '&Ocirc;',	'ô': '&ocirc;',	'Ò': '&Ograve;',	'ò': '&ograve;',	'Ø': '&Oslash;',	'ø': '&oslash;',	'Ù': '&Ugrave;',	'ù': '&ugrave;',	'Ü': '&Uuml;',	'ü': '&uuml;',	'Ç': '&Ccedil;',	'ç': '&ccedil;',	'Ñ': '&Ntilde;',	'ñ': '&ntilde;',	'Ý': '&Yacute;',	'ý': '&yacute;',	'"': '&quot;', '”': '&quot;',	'<': '&lt;',	'>': '&gt;',	'®': '&reg;',	'©': '&copy;',	'\'': '&apos;', 'ª': '&ordf;', 'º': '&ordm', '°':'&deg;'}
            for item in dicHTML:
                if item in texto:
                    texto = texto.replace(item, dicHTML[item])
            return texto
        else:
            return ''
    
    def initAlgorithm(self, config=None):
        
        # 'INPUTS'
        self.addParameter(
            QgsProcessingParameterString(
                self.COC,
                self.tr('Coordinates of Optical Centers', 'Coordenadas dos Centros Ópticos'),
                defaultValue = '149867.058, 249817.768, 1.825; 149988.309, 249782.867, 1.962; 150055.018, 249757.128, 1.346; 150085.600, 249877.691, 1.559',
                multiLine = True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterString(
                self.AZIMUTH,
                self.tr('Azimuths', 'Azimutes'),
                defaultValue = '''46°10'06.37”, 359°12'12.21”, 338°32'59.40”, 298°46'22.93”''',
                multiLine = True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterString(
                self.ZENITH,
                self.tr('Zenith Angles', 'Ângulos Zenitais'),
                defaultValue = '''72°24'22.25”, 70°43'01.75", 74°17'54.17", 65°04'27.25"''',
                multiLine = True
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.WEIGHT,
                self.tr('Use Weight Matrix (W)', 'Usar Matrix Peso (P)'),
                defaultValue = False
            )
        )
        
        '''
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OPENOUTPUT,
                self.tr('Open output file after executing the algorithm'),
                defaultValue = True
            )
        )
        '''
        
        # 'OUTPUT'
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Adjusted 3D Coordinates', 'Coordenadas 3D Ajustadas'),
                fileFilter = '.xls'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterFileDestination(
                'HTML',
                self.tr('Adjustment Report', 'Relatório de Ajustamento'),
                self.tr('HTML files (*.html)')
            )
        )
    
    def String2CoordList (self, txt):
        while ' ' in txt:
            txt = txt.replace(' ', '')
        Splited = txt.split(';')
        lista = []
        for Coords in Splited:
            Splited2 = Coords.split(',')
            lista_aux = []
            for coord in Splited2:
                lista_aux += [float(coord)]
            lista += [lista_aux]
        return lista

    def String2StringList(self, txt):
        while ' ' in txt:
            txt = txt.replace(' ', '')
        Splited = txt.split(',')
        return Splited

    def dms2dd(self, txt):
        txt = txt.replace(' ','').replace(',','.')
        newtxt =''
        for letter in txt:
            if not letter.isnumeric() and letter != '.' and letter != '-':
                newtxt += '|'
            else:
                newtxt += letter
        lista = newtxt[:-1].split('|')
        lista2 = []
        for item in lista:
            if item != '':
                lista2 += [item]
        if len(lista2) != 3: # GMS
            return None
        else:
            if '-' in lista[0]: 
                return -1*(abs(float(lista2[0])) + float(lista2[1])/60 + float(lista2[2])/3600)
            else:
                return float(lista2[0]) + float(lista2[1])/60 + float(lista2[2])/3600

    def CosDir(self, Az, Z):
        k = sin(Z)*sin(Az)
        m = sin(Z)*cos(Az)
        n = cos(Z)
        return array([[k],[m],[n]])
    
    
    def processAlgorithm(self, parameters, context, feedback):
        
        COs = self.parameterAsString(
            parameters,
            self.COC,
            context
        )
        
        Azimutes = self.parameterAsString(
            parameters,
            self.AZIMUTH,
            context
        )
        
        ÂngulosZenitais = self.parameterAsString(
            parameters,
            self.ZENITH,
            context
        )
        
        usar_peso = self.parameterAsBool(
            parameters,
            self.WEIGHT,
            context
        )
        
        abrir_arquivo = self.parameterAsBool(
            parameters,
            self.OPENOUTPUT,
            context
        )
        
        output = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
        )
        
        html_output = self.parameterAsFileOutput(
            parameters, 
            self.HTML, 
            context
        )
        
        # Pontos
        Coords = self.String2CoordList(COs)
        
        # Azimutes (radianos)
        Az = []
        for item in self.String2StringList(Azimutes):
            Az += [self.dms2dd(item)]
        Az = radians(array(Az))
        
        # Ângulos Zenitais (radianos)
        Z = []
        for item in self.String2StringList(ÂngulosZenitais):
            Z += [self.dms2dd(item)]
        Z = radians(array(Z))
        
        # Validação dos dados de entrada
        if not (len(Coords) == len(Az) and len(Az) == len(Z)):
            raise QgsProcessingException(self.tr('Wrong number of parameters!', 'Número de parâmetros errado!'))
        else:
            n = len(Coords)
        # não dever haver valores nulos
        # ângulos entre 0 e 360 graus

        # Montagem do Vetor L
        L = []
        for k in range(len(Coords)):
            L+= [[Coords[k][0]], [Coords[k][1]], [Coords[k][2]]]
        L = array(L)

        # Montagem da Matriz A
        e = 3*n
        p = 3 + n
        A = matrix(zeros([e, p]))
        for k in range(n):
            A[3*k:3*k+3, 0:3] = identity(3)
            A[3*k:3*k+3, 3+k] = self.CosDir(Az[k], Z[k])
        
        # Ajustamento MMQ
        X = pinv(A.T*A)*A.T*L
        V = A*X - L
        sigma2 = (V.T*V)/(e-p)
        SigmaX = sigma2[0,0]*pinv(A.T*A)
        
        if usar_peso:
            Ponto = array(X[0:3, :].T)[0]
            d = []
            for coord in Coords:
                dist = norm(array(coord)-Ponto) 
                d += [1/dist, 1/dist, 1/dist]
            P = diag(d)
            X = pinv(A.T*P*A)*A.T*P*L
            V = A*X - L
            sigma2 = (V.T*P*V)/(e-p)
            SigmaX = sigma2[0,0]*pinv(A.T*P*A)
        
        VAR = str(round(sigma2[0,0],5))
        x = round(float(X[0, 0]),3)
        y = round(float(X[1, 0]),3)
        z = round(float(X[2, 0]),3)
        s_x = round(float(sqrt(SigmaX[0, 0])),4)
        s_y = round(float(sqrt(SigmaX[1, 1])),4)
        s_z = round(float(sqrt(SigmaX[2, 2])),4)
        
        # Resultados
        wb = xlwt.Workbook()
        ws = wb.add_sheet(self.tr("Spreadsheet 1", "Planilha 1"))
        ws.write(0, 0, 'X')
        ws.write(0, 1, 'Y')
        ws.write(0, 2, 'Z')
        ws.write(0, 3, self.tr('type', 'tipo'))
        ws.write(1, 0, x)
        ws.write(1, 1, y)
        ws.write(1, 2, z)
        ws.write(1, 3, self.tr('Adjusted 3D Coordinates', 'Coordenadas 3D Ajustadas'))
        for k in range(len(Coords)):
            ws.write(2+k, 0, Coords[k][0])
            ws.write(2+k, 1, Coords[k][1])
            ws.write(2+k, 2, Coords[k][2])
            ws.write(2+k, 3, self.tr('Station', 'Estação') + ' ' + str(k+1))
        wb.save(output)
        
        
        texto = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
  <title>''' + self.tr('Estimate 3D Coordinates', self.str2HTML('Estimação de Coordenadas 3D')) + '''</title>
</head>
<body
 style="color: rgb(0, 0, 0); background-color: rgb(255, 255, 204);"
 alink="#000099" link="#000099" vlink="#990099">
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span
 style="font-size: 12pt; line-height: 107%;">''' + self.tr('ESTIMATE 3D COORDINATES', 'ESTIMA&Ccedil;&Atilde;O DE COORDENADAS 3D') + '''<o:p></o:p></span></b></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><i>''' + self.tr('Minimum Distance Method', 'M&eacute;todo das Dist&acirc;ncias M&iacute;nimas') + '''<o:p></o:p></i></p>
<o:p>&nbsp;</o:p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><u>''' + self.tr('REPORT','RELAT&Oacute;RIO') + '''<o:p></o:p></u></b></p>
<p class="MsoNormal"><o:p>&nbsp;</o:p></p>
<p class="MsoListParagraph"
 style="text-indent: -18pt; text-align: center;"><!--[if !supportLists]--><b><span
 style=""><span style="">1.<span
 style="font-family: &quot;Times New Roman&quot;; font-style: normal; font-variant: normal; font-weight: normal; font-size: 7pt; line-height: normal; font-size-adjust: none; font-stretch: normal;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</span></span></span></b><!--[endif]--><b>''' + self.tr('Inputs', 'Dados de Entrada') + '''<o:p></o:p></b></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="font-style: italic;">''' + self.tr('Coordinates of the Optical Centers','Coordenadas dos Centros &Oacute;pticos')+ '''</span><o:p></o:p></p>
<div align="center">
<table class="MsoTableGrid"
 style="border: medium none ; border-collapse: collapse;"
 border="0" cellpadding="0" cellspacing="0">
  <tbody>
    [tabela 1]
  </tbody>
</table>
</div>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="font-style: italic;">''' + self.tr('Azimuths','Azimutes') + '''</span><o:p></o:p></p>
<div align="center">
<table class="MsoTableGrid"
 style="border: medium none ; border-collapse: collapse;"
 border="0" cellpadding="0" cellspacing="0">
  <tbody>
    [tabela 2]
  </tbody>
</table>
</div>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="font-style: italic;">''' + self.tr('Zenith Angles', '&Acirc;ngulos Zenitais') + '''</span><o:p></o:p></p>
<div align="center">
<table class="MsoTableGrid"
 style="border: medium none ; border-collapse: collapse;"
 border="0" cellpadding="0" cellspacing="0">
  <tbody>
    [tabela 3]
  </tbody>
</table>
</div>
<p class="MsoNormal" style="text-align: center;"
 align="center"><o:p>&nbsp;</o:p></p>
<p class="MsoListParagraph"
 style="text-indent: -18pt; text-align: center;"><!--[if !supportLists]--><b><span
 style=""><span style="">2.<span
 style="font-family: &quot;Times New Roman&quot;; font-style: normal; font-variant: normal; font-weight: normal; font-size: 7pt; line-height: normal; font-size-adjust: none; font-stretch: normal;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
</span></span></span></b><!--[endif]--><b>'''+ self.tr('Adjustment','Ajustamento') + '''<o:p></o:p></b></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="font-style: italic;">'''+ self.tr('Residuals (V)', 'Res&iacute;duos (V)') + '''</span><o:p></o:p></p>
<div align="center">
<table class="MsoTableGrid"
 style="border: medium none ; border-collapse: collapse;"
 border="1" cellpadding="0" cellspacing="0">
  <tbody>
    [tabela 4]
  </tbody>
</table>
</div>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="font-style: italic;">''' + self.tr('Posteriori Variance', 'Vari&acirc;ncia a posteriori') + ''': &nbsp;</span>[VAR]<o:p></o:p></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="font-style: italic;">''' + self.tr('Adjusted Coordinates and Precisions', 'Coordenas Ajustados e Precis&otilde;es') + '''</span><o:p></o:p></p>
<div align="center">
<table class="MsoTableGrid"
 style="border: medium none ; width: 100.7pt; border-collapse: collapse;"
 border="1" cellpadding="0" cellspacing="0"
 width="134">
  <tbody>
    <tr style="">
      <td
 style="border: 1pt solid windowtext; padding: 0cm 5.4pt; width: 38.9pt;"
 valign="top" width="52">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">X<o:p></o:p></p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 28.75pt;"
 valign="top" width="38">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[X]<o:p></o:p></p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 33.05pt;"
 valign="top" width="44">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[sX]<o:p></o:p></p>
      </td>
    </tr>
    <tr style="">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 38.9pt;"
 valign="top" width="52">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">Y<o:p></o:p></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 28.75pt;"
 valign="top" width="38">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[Y]<o:p></o:p></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 33.05pt;"
 valign="top" width="44">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[sY]<o:p></o:p></p>
      </td>
    </tr>
    <tr style="">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 38.9pt;"
 valign="top" width="52">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">Z<o:p></o:p></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 28.75pt;"
 valign="top" width="38">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[Z]<o:p></o:p></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 33.05pt;"
 valign="top" width="44">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[sZ]<o:p></o:p></p>
      </td>
    </tr>
  </tbody>
</table>
</div>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="font-style: italic;">''' + self.tr('Weight Matrix','Matriz Peso') + ''': [PESO]</span><o:p></o:p></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><i><span
 style="font-size: 10pt; line-height: 107%; color: rgb(127, 127, 127);">*
Obs.: ''' + self.tr('The inverse of the distances to the diagonal of the Weight Matrix is considered.', '&Eacute; considerado o inverso das dist&acirc;ncias para a diagonal da Matriz Peso.') + '''<o:p></o:p></span></i></p>
<p class="MsoNormal"><o:p>&nbsp;</o:p></p>
<p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: right;"
 align="right"><b>Leandro Fran&ccedil;a<o:p></o:p></b></p>
<p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: right;"
 align="right"><b>''' + self.tr('Cartographic Engineer', 'Eng. Cart&oacute;grafo') + '''<o:p></o:p></b></p>
<p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: right;"
 align="right"><b><a
 href="http://www.facebook.com/GEOCAPT">www.facebook.com/GEOCAPT</a>
<o:p></o:p></b></p>
</body>
</html>
        '''
        
        template1 = '''<tr style="">
      <td style="padding: 0cm 5.4pt; width: 460.2pt;"
 valign="top" width="614">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[SUBS]<o:p></o:p></p>
      </td>
    </tr>
        '''
        
        template2 = '''<tr style="">
      <td
 style="border: 1pt solid windowtext; padding: 0cm 5.4pt; width: 39.3pt;"
 valign="top" width="52">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[V_X]<o:p></o:p></p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 46.05pt;"
 valign="top" width="61">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[V_x]<o:p></o:p></p>
      </td>
    </tr>
    <tr style="">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 39.3pt;"
 valign="top" width="52">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[V_Y]<o:p></o:p></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 46.05pt;"
 valign="top" width="61">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[V_y]<o:p></o:p></p>
      </td>
    </tr>
    <tr style="">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 39.3pt;"
 valign="top" width="52">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[V_Z]<o:p></o:p></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 46.05pt;"
 valign="top" width="61">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[V_z]<o:p></o:p></p>
      </td>
    </tr>
        '''
        
        # Preenchimento das tabelas
        table1 = ''
        for coord in Coords:
            tableRowN = template1
            itens  = {
                         '[SUBS]' : str(coord),
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            table1 += tableRowN
            
        table2 = ''
        for azimute in self.String2StringList(Azimutes):
            tableRowN = template1
            itens  = {
                         '[SUBS]' : self.str2HTML(azimute),
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            table2 += tableRowN
        
        table3 = ''
        for zenite_ang in self.String2StringList(ÂngulosZenitais):
            tableRowN = template1
            itens  = {
                         '[SUBS]' : self.str2HTML(zenite_ang),
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            table3 += tableRowN
        
        table4 = ''
        for k in range(len(Coords)):
            vx = V[3*k,0]
            vy = V[3*k+1,0]
            vz = V[3*k+2,0]
            tableRowN = template2
            itens  = {
                         '[V_x]' : str(round(vx,3)),
                         '[V_y]' : str(round(vy,3)),
                         '[V_z]' : str(round(vz,3)),
                         '[V_X]' : 'Vx_' + str(k+1),
                         '[V_Y]' : 'Vy_' + str(k+1),
                         '[V_Z]' : 'Vz_' + str(k+1),
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            table4 += tableRowN
        
        texto = texto.replace('[tabela 1]', table1).replace('[tabela 2]', table2).replace('[tabela 3]', table3).replace('[tabela 4]', table4)
        texto = texto.replace('[PESO]', self.tr('Yes', 'Sim') if usar_peso else self.tr('No', self.str2HTML('Não')))
        texto = texto.replace('[VAR]', VAR)
        texto = texto.replace('[X]', str(x)).replace('[Y]', str(y)).replace('[Z]', str(z)).replace('[sX]', str(s_x)).replace('[sY]', str(s_y)).replace('[sZ]', str(s_z))
        # Exportar HTML
        arq = open(html_output, 'w')
        arq.write(texto)
        arq.close()
        
        feedback.pushInfo(self.tr('Operation completed successfully!', 'Operação finalizada com sucesso!'))
        feedback.pushInfo(self.tr('Leandro França - Eng Cart', 'Leandro Franca - Cartographic Engineer'))
        
        '''
        if abrir_arquivo:
            layer = QgsVectorLayer(output, self.tr("Adjusted 3D Coordinates"), "ogr")
            QgsProject.instance().addMapLayer(layer)
        '''
        
        return {self.OUTPUT: output,
                self.HTML: html_output}
