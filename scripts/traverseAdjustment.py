# -*- coding: utf-8 -*-

"""
traverseAdjustment.py
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
__date__ = '2019-11-17'
__copyright__ = '(C) 2019, Leandro França'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterFileDestination,
                       QgsFields,
                       QgsField,
                       QgsWkbTypes,
                       QgsFeature,
                       QgsGeometry,
                       QgsPoint,
                       QgsApplication
                       )
from numpy import radians, arctan, pi, sin, cos, matrix, sqrt, degrees, array, diag, ones, zeros, floor
from numpy.linalg import norm, pinv, inv


class TraverseAdjustment(QgsProcessingAlgorithm):
    A = 'A'
    B = 'B'
    Y = 'Y'
    Z = 'Z'
    DIST = 'DIST'
    ANGS = 'ANGS'
    DIST_PREC = 'DIST_PREC'
    PPM = 'PPM'
    ANGS_PREC = 'ANGS_PREC'
    CRS = 'CRS'
    OUTPUT = 'OUTPUT'
    HTML = 'HTML'
    rho = 180*3600/pi

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
        return TraverseAdjustment()

    def name(self):
        return 'traverseadjustment'

    def displayName(self):
        return self.tr('Traverse Adjustment', 'Poligonal Enquadrada')

    def group(self):
        return self.tr('LF Survey', 'LF Agrimensura')

    def groupId(self):
        return 'lf_survey'

    def shortHelpString(self):
        return self.tr("""""")
        
    def shortHelpString(self):
        txt_en = 'This algorithm performs the traverse adjustments of a framed polygonal by least squares method, where  the distances, angles, and directions observations are adjusted simultaneously, providing the most probable values for the given data set.  Futhermore, the observations can be rigorously weighted based on their estimated errors and adjusted accordingly.'
        txt_pt = 'Este algoritmo realiza o ajustamento de poligonal enquadrada pelo método dos mínimos quadrados, onde as observações de distâncias, ângulos e direções são ajustadas simultaneamente, fornecendo os valores mais prováveis para o conjunto de dados. Além disso, as observações podem ser rigorosamente ponderadas considerando os erros estimados e ajustados.'
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
            QgsProcessingParameterString(
                self.A,
                self.tr('A: first (E,N) coordinates'),
                defaultValue = '150000, 250000'
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.B,
                self.tr('B: second (E,N) coordinates'),
                defaultValue = '149922.119, 249875.269'
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.Y,
                self.tr('Y: penultimate (E,N) coordinates'),
                defaultValue = '150347.054, 249727.281'
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.Z,
                self.tr('Z: final (E,N) coordinates'),
                defaultValue = '150350.201, 249622.000'
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.DIST,
                self.tr('Distances (d) list'),
                defaultValue = '110.426, 72.375, 186.615, 125.153, 78.235, 130.679, 110.854',
                multiLine = True
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                self.ANGS,
                self.tr('Angles (angs) list'),
                defaultValue = '''75°23'34", 202°4'36", 56°51'15", 283°31'32", 242°57'31", 185°5'12", 94°11'35", 266°13'20" ''',
                multiLine = True
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.DIST_PREC,
                self.tr('Initial distance precision (mm)'),
                type = 1,
                defaultValue = 3
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.PPM,
                self.tr('PPM distance precision'),
                type = 1,
                defaultValue = 3
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGS_PREC,
                self.tr('Angular precision (seconds)'),
                type = 1,
                defaultValue = 10
            )
        )

        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                self.tr('Grid CRS'),
                'ProjectCrs'))

        # OUTPUT
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
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

    def String2NumberList (self, txt):
        while ' ' in txt:
            txt = txt.replace(' ', '')
        Splited = txt.split(',')
        lista = []
        for item in Splited:
            lista += [float(item)]
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

    def azimute(self, A,B):
        # Cálculo dos Azimutes entre dois pontos (Vetor AB origem A extremidade B)
        if ((B[0]-A[0])>=0 and (B[1]-A[1])>0): #1º quadrante
            AzAB=arctan((B[0]-A[0])/(B[1]-A[1]))
            AzBA=AzAB+pi
        elif ((B[0]-A[0])>0 and(B[1]-A[1])<0): #2º quadrante
            AzAB=pi+arctan((B[0]-A[0])/(B[1]-A[1]))
            AzBA=AzAB+pi
        elif ((B[0]-A[0])<=0 and(B[1]-A[1])<0): #3º quadrante
            AzAB=arctan((B[0]-A[0])/(B[1]-A[1]))+pi
            AzBA=AzAB-pi
        elif ((B[0]-A[0])<0 and(B[1]-A[1])>0): #4º quadrante
            AzAB=2*pi+arctan((B[0]-A[0])/(B[1]-A[1]))
            AzBA=AzAB+pi
        elif ((B[0]-A[0])>0 and(B[1]-A[1])==0): # no eixo positivo de x (90º)
            AzAB=pi/2
            AzBA=1.5*pi
        else: # ((B[0]-A[0])<0 and(B[1]-A[1])==0) # no eixo negativo de x (270º)
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

    def DifAz(self, Az_ini, Az_fim):
        # Diferença (ângulo) entre azimutes
        dAz = Az_fim - Az_ini
        if dAz < 0:
            dAz = 2*pi + Az_fim - Az_ini
        return dAz

    # F(Xo) para distâncias:
    def F_X_d(self, pnts, B, Y):
        F_X = [[sqrt((B[0]-pnts[0][0])**2 + (B[1]-pnts[0][1])**2)]]
        for k in range(len(pnts)-1):
            x1 = pnts[k][0]
            y1 = pnts[k][1]
            x2 = pnts[k+1][0]
            y2 = pnts[k+1][1]
            F_X += [[sqrt((x1-x2)**2 + (y1-y2)**2)]]
        F_X += [[sqrt((Y[0]-pnts[-1][0])**2 + (Y[1]-pnts[-1][1])**2)]]
        return F_X

    # F(Xo) para ângulos:
    def F_X_a(self, pnts, A, B, Y, Z):
        pnts2 = [B] + pnts + [Y]
        # leitura do ângulo no sentido horário
        F_X = [[3600*degrees(self.DifAz(self.azimute(B, A)[0], self.azimute(B,pnts[0])[0]))]]
        for k in range(len(pnts2)-2):
            pnt0 = pnts2[k]
            pnt1 = pnts2[k+1]
            pnt2 = pnts2[k+2]
            F_X += [[3600*degrees(self.DifAz(self.azimute(pnt1,pnt0)[0], self.azimute(pnt1, pnt2)[0]))]]
        F_X += [[3600*degrees(self.DifAz(self.azimute(Y, pnts2[-2])[0], self.azimute(Y, Z)[0]))]]
        return F_X

    def Jacobiana_d(self, pnts, B, Y, n_d, n_par):
        Jac = zeros([n_d, n_par])
        pnts2 = [B] + pnts + [Y]
        for k in range(n_d):
            I = pnts2[k]
            J = pnts2[k+1]
            IJ = norm(array(J) - array(I))
            linha = [(I[0]-J[0])/IJ, (I[1]-J[1])/IJ, (J[0]-I[0])/IJ, (J[1]-I[1])/IJ]
            if k == 0:
                Jac[k, 0:2] = linha[2:]
            elif k < (n_d-1):
                Jac[k, (2*k-2):(2*k-2 + 4)] = linha
            else:
                Jac[k, (2*k-2):(2*k-2 + 2)] = linha[:2]
        return list(Jac)

    def Jacobiana_a(self, pnts, A, B, Y, Z, n_angs, n_par):
        Jac = zeros([n_angs, n_par])
        pnts2 = [A, B] + pnts + [Y, Z]
        for k in range(n_angs):
            B = pnts2[k]
            I = pnts2[k+1]
            F = pnts2[k+2]
            IB = norm(array(B) - array(I))
            IF = norm(array(F) - array(I))
            linha = [(I[1]-B[1])/IB**2, (B[0]-I[0])/IB**2, (B[1]-I[1])/IB**2 - (F[1]-I[1])/IF**2,
                     (I[0]-B[0])/IB**2 - (I[0]-F[0])/IF**2, (F[1]-I[1])/IF**2, (I[0]-F[0])/IF**2]
            linha = list(self.rho*array(linha))
            if n_par > 2:
                if k == 0:
                    Jac[k, 0:2] = linha[4:]
                elif k==1:
                    Jac[k, 0:4] = linha[2:]
                elif k < (n_angs-2):
                    Jac[k, (2*k-4):(2*k-4 + 6)] = linha
                elif k == n_angs-2:
                    Jac[k, (2*k-4):(2*k-4 + 4)] = linha[:4]
                else:
                    Jac[k, (2*k-4):(2*k-4 + 2)] = linha[:2]
            else:
                if k == 0:
                    Jac[0, 0:2] = linha[4:]
                elif k == 1:
                    Jac[1, 0:2] = linha[2:4]
                elif k == 2:
                    Jac[2, 0:2] = linha[:2]
        return list(Jac)

    def processAlgorithm(self, parameters, context, feedback):

        A = self.parameterAsString(
            parameters,
            self.A,
            context
        )
        A = self.String2NumberList(A)

        B = self.parameterAsString(
            parameters,
            self.B,
            context
        )
        B = self.String2NumberList(B)

        Y = self.parameterAsString(
            parameters,
            self.Y,
            context
        )
        Y = self.String2NumberList(Y)

        Z = self.parameterAsString(
            parameters,
            self.Z,
            context
        )
        Z = self.String2NumberList(Z)

        d = self.parameterAsString(
            parameters,
            self.DIST,
            context
        )
        d = self.String2NumberList(d)
        feedback.pushInfo('Distances list: ' + str(d))

        angs = self.parameterAsString(
            parameters,
            self.ANGS,
            context
        )
        angs = self.String2StringList(angs)
        feedback.pushInfo('Angles list: ' + str(angs))
        lista = []
        for ang in angs:
            lista += [3600*float(self.dms2dd(ang))]
        angs = lista


        dist_precision = self.parameterAsDouble(
            parameters,
            self.DIST_PREC,
            context
        )
        dist_precision *= 1e-3 # milimeter to meters

        ppm = self.parameterAsDouble(
            parameters,
            self.PPM,
            context
        )
        ppm *= 1e-6 # ppm

        ang_precision = self.parameterAsDouble(
            parameters,
            self.ANGS_PREC,
            context
        )

        CRS = self.parameterAsCrs(
            parameters,
            self.CRS,
            context
        )

        # OUTPUT
        Fields = QgsFields()
        Fields.append(QgsField('id', QVariant.Int))
        GeomType = QgsWkbTypes.Point
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

        html_output = self.parameterAsFileOutput(
            parameters,
            self.HTML,
            context
        )

        # Precisões
        sd_d = list(dist_precision + array(d)*ppm)
        sd_a = list(ang_precision*ones(len(angs)))

        # Observações
        Lb = matrix(d + angs).reshape([len(d)+len(angs),1])

        # Cálculo de aproximações inicias
        Xo = []
        pnts = []
        Az0 = self.azimute(B,A)[0]
        p0 = B
        for k in range(len(d)-1):
            ang = pi/2 - Az0 - radians(angs[k]/3600) # leitura do ângulo no sentido horário
            x = p0[0] + d[k]*cos(ang)
            y = p0[1] + d[k]*sin(ang)
            Xo += [[x], [y]]
            pnts += [(x, y)]
            Az0 = -pi/2 - ang
            p0 = (x, y)
        pnts_ini = pnts

        # Cálculo do Erro de Fechamento Linear
        ang = pi/2 - Az0 - radians(angs[-2]/3600)
        x = p0[0] + d[-1]*cos(ang)
        y = p0[1] + d[-1]*sin(ang)
        Y_ = (x, y)
        Erro = array(Y_)-array(Y)
        feedback.pushInfo('Linear closure error: ' + str(round(norm(array(Y_)-array(Y)),4)) + ' m')
        feedback.pushInfo('E and N errors: ' + str((round(Erro[0],4),round(Erro[1],4))) + ' m')

        # Cálculo do Erro de Azimute
        Az0 = self.azimute(B,A)[0]
        for k in range(len(angs)):
            ang = pi/2 - Az0 - radians(angs[k]/3600) # leitura do ângulo no sentido horário
            Az = pi/2 - ang
            Az0 = Az -pi
        if Az<0 or Az>2*pi:
            if (Az<0):
               Az=Az+2*pi
            else:
               Az=Az-2*pi
        feedback.pushInfo('Angular closure error: ' + str(round(3600*(degrees(Az - self.azimute(Y,Z)[0])),2)) + ' sec')

        # Dados para matrix jacobiana
        n_par = len(pnts)*2
        n_d = len(d)
        n_angs = len(angs)
        n_obs = n_d + n_angs

        # Matriz Peso
        P = matrix(diag(array(sd_d + sd_a)**(-2)))

        # Cálculo iterativo das Coordenadas (Parâmetros)
        cont = 0
        cont_max = 10
        tol = 1e-4

        while cont < cont_max:
            F_Xo = self.F_X_d(pnts, B, Y) + self.F_X_a(pnts, A, B, Y, Z)
            J = matrix(list(self.Jacobiana_d(pnts, B, Y, n_d, n_par)) + list(self.Jacobiana_a(pnts, A, B, Y, Z, n_angs, n_par)))
            L = matrix(Lb - F_Xo)
            delta = pinv(J.T*P*J)*J.T*P*L
            Xa = array(Xo) + array(delta)
            cont += 1
            #print('Iteração:', cont, '\ncoord:', Xa.T, '\ndelta:', delta.T)
            feedback.pushInfo('Iteração: ' + str( cont) + '\nCoord: ' + str(Xa.T) + '\nDelta:' + str(delta.T))
            if max(abs(delta))[0,0] > tol:
                Xo = Xa
                pnts = []
                for k in range(int(len(Xo)/2)):
                    pnts += [(float(Xo[2*k][0]), float(Xo[2*k+1][0]))]
            else:
                break

        # Resíduos
        V = Lb - F_Xo

        # Sigma posteriori
        n = len(Lb) # número de observações
        u = len(Xa) # número de parâmetros
        sigma2 = V.T*P*V/(n-u)

        # Observações Ajustadas (La)
        La = Lb + V

        # MVC de Xa
        SigmaXa = sigma2[0,0]*pinv(J.T*P*J)

        # MVC de La
        SigmaLa = J*SigmaXa*J.T

        # MVC de Lb
        var_priori = 1.0
        SigmaLb = var_priori*inv(P)

        # MVC dos resíduos
        SigmaV = SigmaLa + SigmaLb


        feature = QgsFeature()
        total = 100.0 /len(pnts)  if len(pnts) else 0
        for current, pnt in enumerate(pnts):
            geom = QgsGeometry(QgsPoint(float(pnt[0]), float(pnt[1])))
            feature.setGeometry(geom)
            feature.setAttributes([current+1])
            sink.addFeature(feature, QgsFeatureSink.FastInsert)
            if feedback.isCanceled():
                break
            feedback.setProgress(int(current * total))

       # Relatório
        tabela1 = '''    <tr style="">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 48.1pt;"
 valign="top" width="64">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; line-height: normal;"><span
 style="" lang="EN-US">[En]<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 70.4pt;"
 valign="top" width="94">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: right; line-height: normal;"
 align="right"><span style="" lang="EN-US">[X]<o:p></o:p></span></p>
      </td>
    </tr>
    <tr style="">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 48.1pt;"
 valign="top" width="64">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; line-height: normal;"><span
 style="" lang="EN-US">[Nn]<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 70.4pt;"
 valign="top" width="94">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: right; line-height: normal;"
 align="right"><span style="" lang="EN-US">[Y]<o:p></o:p></span></p>
      </td>
    </tr>
'''
        tabela2 = '''<tr style="">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 48.1pt;"
 valign="top" width="64">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; line-height: normal;"><span
 style="" lang="EN-US">[En]<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 112.7pt;"
 valign="top" width="150">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: right; line-height: normal;"
 align="right"><span style="" lang="EN-US">[X]<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 102.05pt;"
 valign="top" width="136">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: right; line-height: normal;"
 align="right"><span style="" lang="EN-US">[sdx]<o:p></o:p></span></p>
      </td>
    </tr>
    <tr style="">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 48.1pt;"
 valign="top" width="64">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; line-height: normal;"><span
 style="" lang="EN-US">[Nn]<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 112.7pt;"
 valign="top" width="150">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: right; line-height: normal;"
 align="right"><span style="" lang="EN-US">[Y]<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 102.05pt;"
 valign="top" width="136">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: right; line-height: normal;"
 align="right"><span style="" lang="EN-US">[sdy]<o:p></o:p></span></p>
      </td>
    </tr>
'''
        tabela3 = '''<tr style="">
      <td
 style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 84.9pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">[obs]<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 84.95pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">[r]<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 117.6pt;"
 valign="top" width="157">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">[adj_obs]<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 102.05pt;"
 valign="top" width="136">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">[sd]<o:p></o:p></span></p>
      </td>
    </tr>
'''

        texto = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
  <title></title>
</head>
<body>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><u><span
 style="font-size: 12pt; line-height: 107%;" lang="EN-US">TRAVERSE
ADJUSTMENT<o:p></o:p></span></u></b></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><span style="" lang="EN-US"><o:p>&nbsp;</o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span style="" lang="EN-US">Initial
approximation<o:p></o:p></span></b></p>
<div align="center">
<table class="MsoTableGrid"
 style="border: medium none ; border-collapse: collapse;"
 border="1" cellpadding="0" cellspacing="0">
  <tbody>
    <tr style="">
      <td
 style="border: 1pt solid windowtext; padding: 0cm 5.4pt; width: 48.1pt;"
 valign="top" width="64">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">Station<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 70.4pt;"
 valign="top" width="94">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">Coordinates<o:p></o:p></span></p>
      </td>
    </tr>
    [table1]
  </tbody>
</table>
</div>
<p class="MsoNormal" style=""><span style=""
 lang="EN-US"><o:p>&nbsp;</o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span style="" lang="EN-US">Adjustment<o:p></o:p></span></b></p>
<div align="center">
<table class="MsoTableGrid"
 style="border: medium none ; border-collapse: collapse;"
 border="1" cellpadding="0" cellspacing="0">
  <tbody>
    <tr style="">
      <td
 style="border: 1pt solid windowtext; padding: 0cm 5.4pt; width: 48.1pt;"
 valign="top" width="64">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">Station<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 112.7pt;"
 valign="top" width="150">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">Adjusted
Coordinates<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 102.05pt;"
 valign="top" width="136">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">Standard
Deviation<o:p></o:p></span></p>
      </td>
    </tr>
    [table2]
  </tbody>
</table>
</div>
<p class="MsoNormal" style="text-align: center;"><span
 style="" lang="EN-US"><o:p></o:p></span><br>
<i><span style="" lang="EN-US">Posteriori
variance</span></i><span style="" lang="EN-US">:
<span style="color: red;">[sigma2]</span><o:p></o:p></span></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span style="" lang="EN-US"></span></b></p>
<p class="MsoNormal" style="text-align: center;"
 align="center"><b><span style="" lang="EN-US">Observations<o:p></o:p></span></b></p>
<div align="center">
<table class="MsoTableGrid"
 style="border: medium none ; width: 389.5pt; border-collapse: collapse;"
 border="1" cellpadding="0" cellspacing="0"
 width="519">
  <tbody>
    <tr style="">
      <td
 style="border: 1pt solid windowtext; padding: 0cm 5.4pt; width: 84.9pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">Observations<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 84.95pt;"
 valign="top" width="113">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">Residuals<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 117.6pt;"
 valign="top" width="157">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">Adjusted
Observations<o:p></o:p></span></p>
      </td>
      <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 102.05pt;"
 valign="top" width="136">
      <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><span style="" lang="EN-US">Standard
Deviation<o:p></o:p></span></p>
      </td>
    </tr>
    [table3]
  </tbody>
</table>
</div>
<p class="MsoNormal" style=""><span style=""
 lang="EN-US"><o:p>&nbsp;</o:p></span></p>
<p class="MsoNormal" style=""><span style=""
 lang="EN-US"><o:p>&nbsp;</o:p></span></p>
<p class="MsoNormal" style="margin-bottom: 0.0001pt;"><b><span
 style="" lang="EN-US">Leandro Fran&ccedil;a<o:p></o:p></span></b></p>
<p class="MsoNormal" style="margin-bottom: 0.0001pt;"><span
 style="" lang="EN-US">Cartographic Engineer<o:p></o:p></span></p>
<p class="MsoNormal" style="margin-bottom: 0.0001pt;"><i><span
 style="" lang="EN-US"><a
 href="mailto:geoleandro.franca@gmail.com">geoleandro.franca@gmail.com</a>
<o:p></o:p></span></i></p>
</body>
</html>
'''

        # Aproximação inicial
        cont = 0
        table1 = ''
        for pnt in pnts_ini:
            X = pnt[0]
            Y = pnt[1]
            cont += 1
            tableRowN = tabela1
            itens  = {
                         '[En]' : 'E' + str(cont),
                         '[Nn]': 'N' + str(cont),
                         '[X]': str(round(X,3)),
                         '[Y]': str(round(Y,3))
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            table1 += tableRowN

        # Ajustamento
        cont = 0
        table2 = ''
        SD = SigmaXa.diagonal()
        for k in range(len(pnts_ini)):
            X = Xa[2*k, 0]
            Y = Xa[2*k+1, 0]
            sdx = sqrt(SD[0, 2*k])
            sdy = sqrt(SD[0, 2*k+1])
            cont += 1
            tableRowN = tabela2
            itens  = {
                         '[En]' : 'E' + str(cont),
                         '[Nn]': 'N' + str(cont),
                         '[X]': str(round(X,3)),
                         '[Y]': str(round(Y,3)),
                         '[sdx]': str(round(sdx,3)),
                         '[sdy]': str(round(sdy,3)),
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            table2 += tableRowN

        # Observações
        table3 = ''
        SD = SigmaLa.diagonal()
        for k in range(n_d): # Distâncias
            obs = Lb[k, 0]
            adj_obs = La[k, 0]
            sd = sqrt(SD[0, k])
            r = V[k, 0]
            cont += 1
            tableRowN = tabela3
            itens  = {
                         '[obs]' : str(round(obs,3)),
                         '[r]': str(round(r,4)),
                         '[adj_obs]': str(round(adj_obs,3)),
                         '[sd]': str(round(sd,3))
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            table3 += tableRowN
        for t in range(k+1, k+1+ n_angs): # Ângulos
            obs = Lb[t, 0]
            adj_obs = La[t, 0]
            sd = sqrt(SD[0, t])
            r = V[t, 0]
            cont += 1
            tableRowN = tabela3
            itens  = {
                         '[obs]' : self.str2HTML(self.dd2dms(obs/3600,3)),
                         '[r]': str(round(r,4)) + '"',
                         '[adj_obs]': self.str2HTML(self.dd2dms(adj_obs/3600,3)),
                         '[sd]': str(round(sd,3)) + '"'
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            table3 += tableRowN

        # Documento prinicipal
        itens  = {
                         '[table1]': table1,
                         '[table2]': table2,
                         '[table3]': table3,
                         '[sigma2]': str(round(sigma2[0,0],3))
                         }
        for item in itens:
            texto = texto.replace(item, itens[item])

        # Exportar HTML
        arq = open(html_output, 'w')
        arq.write(texto)
        arq.close()

        feedback.pushInfo(self.tr('\nOperation completed successfully!'))
        feedback.pushInfo('Leandro França - Eng Cart\n')
        return {self.OUTPUT: dest_id,
                    self.HTML: html_output}
