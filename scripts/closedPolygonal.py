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
        return ClosedPolygonal()

    def name(self):
        return 'planimetry'

    def displayName(self):
        return self.tr('Closed Polygonal', 'Poligonal Fechada')

    def group(self):
        return self.tr('LF Survey', 'LF Agrimensura')

    def groupId(self):
        return 'lf_survey'

    def shortHelpString(self):
        return self.tr("")
    
    def shortHelpString(self):
        txt_en = 'Calculates the adjusted coordinates from angles and horizontal distances of a Closed Polygonal'
        txt_pt = 'Cálculo das coordenadas ajustadas a partir de medições de ângulos e distâncias de uma poligonal fechada.'
        dic_BW = {'face': 'iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMMwAADDMBUlqVhwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAIUSURBVEiJvZa9quJAGIbfMfEYTUSUQAqLYOnehJobsBTlHLbRQtKKlY3lObegxRa7pRdg7y0saiuoKAErMZif2Squ2eTEOCfsC1Pk+3uYb2YyQwCg1+u9UUqHAKoAOCQrB8ASwPt0Ov1JdF3/bprmj4QhoXp5eXnjTdMcUEr/Bw+WZQ15Smn1q4UIIZBlGaIoghBys2+3W1yv19u367rfeAAc6ww5jkOz2USj0YAoigH/aDTCbrfzpfCUUrAC2+02NE2LjPm3NjNQkiTU6/WHsFAgi1RVRSqVCthd171BwmozA/P5fMA2n88xm81g2zYAwHGccCAL9H43elosFrhcLpE5zMCwHMdxImtRSp8DptNpZDIZAIAgCAG/IAi+42Ga5q29nkin06FxgZqmodvtxooFgPF4jPV67bM9NcNnW384HJI7h49kWRZOp9PXgOfzGfv9HgCQy+VQKBR8fsMwYFkWAOB4PMJ13UAN0mq1Yq/hfVytVoOu6z7/YDDAZrP5Wzzk6CR6LOLEJLqGcWrxYX2OW5wJmOQOjQX0ApOERgIrlQoTUJblgK1cLodeWZ4IIeDDngZx5P1T75XNZiFJUmQeTyl1wPAW/awrD7rlpDiOW3qL/cz4DBY1CCG/U4qifDw7O1YpivJBAGAymbwahjG0bbtKKeXjJJdKJaiq6rOtVqvAjU8IsTmOWxaLxfd+v//rD1H2cZ8dKhk8AAAAAElFTkSuQmCC', 'github': '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', 'instagram': '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', 'lattes': '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', 'linkedin': 'iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAYAAACpSkzOAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAM6QAADOkBmiiHWwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJRSURBVEiJ7ZU/aCJREMa/t7soa5LOoGihktZOQSxSWykBIYVaWZ6NVa6wSZ/WI5BGziJypA1CQBLsgkKKgBjFQkEtkouJ+AdxdeeKnHvurXdcXK84uK/amfl4v9m3s++xbrdrury8PGm324dEZMYGxRj7arPZvoRCoSPh/Pz8pFqtftgkYEnmTqeT6PV6xDscjs9EZPpLIADAy8uLS5jP52bGGACA4ziEw2H4/X5IkoSrqytcX1/rBhHRrrCcCAaDCAQCShyJRPD6+oq7uzvdMG458Hg8GoPX69UN0YDG47HGsCqnG5TP50FESjyZTFAoFDYCYvF4nBbDAAB7e3vw+XyQJAnFYhGPj4+6IUQE4eekJEm4vb0F8DaFC1mtVphMb3+BLMtotVogItjtdjgcDhiNRvT7fTw8PKzcbhXI5XIhlUqpOkkkEpjP5zg+PoYg/LCfnp5if38fbrdbteB0OsXFxQVubm5+DTIYDKoiYww8z4OIwPO8qhaLxbCzs6Pp3GAwIBqN4vn5Gff390qe0zj/UKsgywqFQqpY843eo1KphHK5DLPZjIODAxiNRqXmdDqxvb2N4XCoD1Sv13F2dqbEs9kM0WhU5bFYLApo7a1bTOZClUpF49na2lKe1wb1ej1VvGqklwdobdB79R/0j4FkWdYYiEh1dawrAcATgF0AaDabyOVyyuE5HA4xmUwAAJlMRjl2ZFlGo9FQLTQajZDNZiGKouKp1WqL8hNLJpPpwWCQ0N3ybySKYpqLxWJHjLFP399s03riOC4dCAQ+fgMeouMzfwx22gAAAABJRU5ErkJggg==', 'RG': 'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAcCAYAAAB2+A+pAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMfwAADH8BdgxfmQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAM2SURBVEiJtZdLSytJFMd/1dXB+OiQRJEQBEnbPgISJGIQcePKjyBZzoP5AH6OuR9gFjPMznwC1650EbKSy00WPhJ8EMlDtG1M0p2axZCA1871cZM/NDRFnfqdqjrnVJUAODg4+E0IsQ8sA5LRyANKQogve3t7/4hcLvcH8NeIYL5SSv2uAftDHhSl1A/7CCH2dWBxWNBoNIppmgSDQarVKufn53ie59d1RQO0YUBjsRg7OztomkatVmNpaYnNzU2EEH7dNX0YUKUUpmlyd3dHPp9HKcXV1RXT09MIIXyXfihgKSWGYVCpVPoQ27axbXugjS/4HcHh29btdlFKsbq6SiwWA6BQKHB/f/82WEpJKpUiEAi8aA8EAiilaLVaNBoNrq+vabfbr+BCCG5vb3l8fCSTyaDr/ov6KrA8z6NcLtNqtUgkEszPz+M4Ds1mE9u2MQyDjY0Ndnd3mZmZ6ds4jkMoFAKg0Wjw8PCAEIJOp+ML9nWnZ5hIJJBSUiqV+gMIIbAsi3Q6zdbWFoeHh7iuS7lcZn19HcdxsG0by7Ko1+sD93lgcCml6Ha7SClftZ+dnbG4uIhhGMzOznJzc0OlUkHTNBYWFtB1nXq9zunp6aA8/lxUe57H09MThmEwPj7ed+ji4oLLy0uEEHieNyiHPw+WUjI5OYlS6lXE9krmj6DwyaplmiaGYVCtVqnX658Z4u0ZCyGIx+O0223GxsaYm5sjHo9Tq9U4OTn5FPRdYCkly8vLCCEIh8MopSgUCpTLZVzXHR3YdV2Ojo7wPI/t7W1isRjBYPCnoPDOPVZK4XlePz2SySThcHj04J4ajQbFYhEpJZlM5lWOjwwMUCwWaTabRCIR0un08MG9gt/778l1XfL5PJ1OB9M0WVlZGR54amoKy7IIBoPouo5lWYRCof7SNptN8vk83W6XVCrF2toaExMTHwKLXC734vCVUpJOp9F1/cW5rGkapVLpRcGIRqMkk0kikQiO43B8fMzz8/O7wd73Mx90EfArg0opNE178/LwnboaUPID+H2DnPkgFOCbppT68lGrn5VS6k8tm83+DfwKfOX/Z8ao5AFflVK/ZLPZf/8DudZq3wvXLmgAAAAASUVORK5CYII=', 'tweeter': 'iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAYAAACpSkzOAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMMQAADDEBLaRWDgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAK5SURBVEiJpZU7T+NAFEZP4kAePBwZ8TA0EUIRKKIgQhSImnZ/wDYr7Q/barddbRu2QVAQhChAgBQqQClwFEIcx8IYfLdKNk5sJ4GRRh6PPN+Z+90749jZ2VnGsqyfwD6QEREARISocdRcT7dF5AD4lmi327+AL0GCn4QgIhkR+SIiPxIish8k3i/yQVCn7ydEJD0sgjDBMUCZxCg2hQmqqsri4iKKotBoNKhWq741vesSvULpdJrJyUkajcZQy7a2tlheXqa3FQoFzs/PmZubQ9M0Dg8Pu2vivQJLS0sUi0Wy2WykFfl8fgACkEql2N3dJZfLcXFxgaqq/0G9O04mk8RiMba3t8nlcqHRrK6uDkB628TEBDs7O5imORgRgGVZ3Y/z+Tx7e3ssLCz4QMlkkng8HglqNpscHBzw9vbmz1EHVK1WWVtb6wpNTU1RLBZ5f3/HMAzq9TqO40RCAGq1Gq7r+jboK4aZmRmurq7Y3Nz0LVQUBV3X0XV9KATAcZwBy7vlLSJomjbU/1Ha8/PzAMhXdQ8PD5+GABiGEQ1qt9tcXl5+CvL09MTLy8ugdf0T9/f32LbNxsYGs7OzY4Our68DD/oASEQoFApMT0+PDTFNk7u7u0BQPAhULpdxXXds0PHxMZ7nDUBCQa1Wi1KpRKVSwTTNkSAnJyfU6/XQWz4QJCI4jsPj4yOKogyFnJ6ecnt7G3nTd3OUSCSYn59HURRUVUXXdTKZTCTAtm2Ojo585dwP6rx3Qa+vrzSbTdbX11lZWSEWi4UCLMvi5uaGSqWC53mh/67esa/qTNOkXC4DoGka2WyWVCoFgOu6tFotDMPAtu3QXISNA8tbRKjVaoEnPCwPYZZ1nnHP8+ww2Ed7P0RE7LjneX/7ff6ocES0pbiIfBWRP57n2aMAwywKGdsi8ltRlO//AFPkniYXwGRMAAAAAElFTkSuQmCC', 'udemy': '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', 'youtube': 'iVBORw0KGgoAAAANSUhEUgAAACEAAAAaCAYAAAA5WTUBAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMNwAADDcBracSlQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAKkSURBVEiJxZcxSBthFIC/918uGhxMsyptcGjoIgGHW9wSihQKGZrNthHsIC7S1TqWgkRwcZV2lKo0FouixaEuEQ4khIIdrClkEoIZgiae93fQgFgll5jqt93x3v++e3f/3TvhGgYHBx/UarUUEAMeA48A/3WxDagBf4A9EdmsVqsfd3d3j64GyeWDZDJpFAqFKWAC6G6haCPKIjKTzWbfA+4/Ev39/V2dnZ3LwNP/UPwqaycnJy9yuVwFQF2cVIFA4PMdCQAMBQKBL8lk0gAwACzLmtJav7kjgTp95XK5ViwWf0g0Gg36/f7fQLBRltYaEWkU5hkRKTmO06dM03ztRaAuEQ6H0Vq3RUJrHTIM46XR29v7jvNt2BClFEtLS0QiEfb39ymVSrfujIg4Cog0mxiPx1lYWGBycpKenh5c122cdANa64gCHra6QCKRYHl5mfHxcYLBII7jtLJMWAEdrUrUSaVSrK6uMjo6SigU4uzsrJn0DtU4xhs+n4+xsTFWVlYYHh6mq6vL821qm0Qd0zSZmJggk8kQi8XuR6LO1tYW+XzeUzd87S6ey+WYnZ0ln88jIijV+DrbJnF4eMj09DTb29u4rtvU+8MHVLnFDjk+PiadTrO+vs7p6WkrS1R9QAGPb8zLaK2Zm5tjcXGRSqXiqe03sO8D9pqVyGQyzM/PUywWMQzjNgIAv3xa600Ree4l2nEcRkZGODg4QCmFYRi3KQ6AiGzIwMBAt2EYB9znp9y27bLWesZjUtsELkjbtl2ur6osy/qqtX7W7io3ISIb2Wx2CHDrT5TrOE4SWLsjgW+O4yS4mLiv9ldZljWptX6Lx2mrSY6A9M7OzgeuG/kvE41Gg6ZpvhKROPCE85mj5Z8fEfnpuu5313U/2bZdvhr0F9Fo9phaoDu9AAAAAElFTkSuQmCC'}
        footer = '''<div align="right">
                      <p align="right"><b>'''+self.tr('Author: Leandro Franca', 'Autor: Leandro França')+'''</b></p>
                      <div align="right">
                      <a target="_blank" rel="noopener noreferrer" href="https://www.udemy.com/user/leandro-luiz-silva-de-franca/"><img title="Udemy" src="data:image/png;base64,'''+dic_BW['udemy']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/GEOCAPT/"><img title="Facebook" src="data:image/png;base64,'''+dic_BW['face']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.youtube.com/channel/UCLrewDGciytcBG9r0OxTW2w"><img title="Youtube" src="data:image/png;base64,'''+dic_BW['youtube']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.researchgate.net/profile/Leandro_Franca2"><img title="ResearchGate" src="data:image/png;base64,'''+dic_BW['RG']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://github.com/LEOXINGU"><img title="GitHub" src="data:image/png;base64,'''+dic_BW['github']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.linkedin.com/in/leandro-fran%C3%A7a-93093714b/"><img title="Linkedin" src="data:image/png;base64,'''+dic_BW['linkedin']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="http://lattes.cnpq.br/8559852745183879"><img title="Lattes" src="data:image/png;base64,'''+dic_BW['lattes']+'''"></a>
                      </div>
                    </div>'''
        return self.tr(txt_en, txt_pt) + footer
    
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
