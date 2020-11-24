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
        return self.tr('Geodetic Landmark Informations', 'Monografia de Marco Geodésico')

    def group(self):
        return self.tr('LF Documents', 'LF Documentos')

    def groupId(self):
        return 'lf_documents'

    def shortHelpString(self):
        return self.tr('', '')
    
    def shortHelpString(self):
        txt_en = 'This tool generates monograph(s) of geodetic landmarks automatically from the "pto_ref_geod_topo_p" layer.'
        txt_pt = 'Esta ferramenta gera monografia(s) de marcos geodésicos de forma automática a partir da camada "pto_ref_geod_topo_p".'
        dic_BW = {'face': 'iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMMwAADDMBUlqVhwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAIUSURBVEiJvZa9quJAGIbfMfEYTUSUQAqLYOnehJobsBTlHLbRQtKKlY3lObegxRa7pRdg7y0saiuoKAErMZif2Squ2eTEOCfsC1Pk+3uYb2YyQwCg1+u9UUqHAKoAOCQrB8ASwPt0Ov1JdF3/bprmj4QhoXp5eXnjTdMcUEr/Bw+WZQ15Smn1q4UIIZBlGaIoghBys2+3W1yv19u367rfeAAc6ww5jkOz2USj0YAoigH/aDTCbrfzpfCUUrAC2+02NE2LjPm3NjNQkiTU6/WHsFAgi1RVRSqVCthd171BwmozA/P5fMA2n88xm81g2zYAwHGccCAL9H43elosFrhcLpE5zMCwHMdxImtRSp8DptNpZDIZAIAgCAG/IAi+42Ga5q29nkin06FxgZqmodvtxooFgPF4jPV67bM9NcNnW384HJI7h49kWRZOp9PXgOfzGfv9HgCQy+VQKBR8fsMwYFkWAOB4PMJ13UAN0mq1Yq/hfVytVoOu6z7/YDDAZrP5Wzzk6CR6LOLEJLqGcWrxYX2OW5wJmOQOjQX0ApOERgIrlQoTUJblgK1cLodeWZ4IIeDDngZx5P1T75XNZiFJUmQeTyl1wPAW/awrD7rlpDiOW3qL/cz4DBY1CCG/U4qifDw7O1YpivJBAGAymbwahjG0bbtKKeXjJJdKJaiq6rOtVqvAjU8IsTmOWxaLxfd+v//rD1H2cZ8dKhk8AAAAAElFTkSuQmCC', 'github': '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', 'instagram': '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', 'lattes': 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAdCAYAAACwuqxLAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAOEwAADhMBVGlxVAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAd/SURBVEiJlVZ7TFTZHf7ua+bOzJ0XwyLDIDLy1oFVg7E2RmPMUmxNscaiQqON0mA0YYORtG7ShFTjxk37h8bQpVmN2d2EdnzABjF2C/VRX2BFVBAyQJPOiEuBGWa4zMy9d+7c0z/Wob5i7C+5ycm5Od/3+53z/b5zKLwUhBD9/fv3a7q7u7cODg7+QBRFi6qq3MzMzCxN036DwfA4Kyure+XKlX9ramqawnsElRoEg8Hlx44du9DX11fMcRxSH0VRCAaDAACO46BpGliWJYSQRzzPX6yoqPjq8OHD/34nQSgUymlqavrn+Pj4B7IsI5FIgBACvV4Po9EISZKgadrDrKysL/Lz8+/yPD/c3NwsvU8FLAC0tLR8pqrqBy6XC4qiQFEUSJKE2dlZxGIx4vF4PmltbT1BURR5H9BXKhgYGFh+/Pjxx3q9nibk+/UMw4AQgtnZWQiC8FlbW9uv/1/ghQouXrxYJYoiPTMzAwDQ6/Uwm80wGo3gOE7au3fv8ba2NkxOTmacO3fuN0NDQyv1er1aUlLyoKqq6ov8/Pyxd1awefPmv87Pz1cAgKZpSCQSMBgMcDgckGX5H11dXevD4bC9vr5+wO/358iyDJ1Oh2QyCUKIUlNT88mhQ4f+AACnT5925Ofn6yorK79LEdCqqi4zmUwwmUwwGAzQ6XRQVRWapgHAJABcuXLlF3Nzczkcx4EQAo7jYLFYYLVadZ2dnb8/ceLEAQDIyMgIt7S0eG/dumVeIDCZTBae56HT6cAwDFiWhcViSW2TDgDC4bDdYDCAoijQNA2DwQCbzYa0tDRYrVbcvHnz02vXrgnV1dVJQRDYo0ePnieE0ABAC4IgpDLneR4OhwPp6ekQBAFGozEDAMrKyv7udruRTCbBcRyMRiOMRiP0ej1YlgUhxHLnzp01AFBaWjo+Nzf3o507d/4KAGiLxRLPyclBdnY2cnJy4HK5kJaWBo7jwLJsmdfrZdatW3crHo//ZdOmTeB5HizLQhRFiKIIRVGQTCYhSVIMABwOxzwhBD6f79OrV6+m0UajUfR4PCgpKUFeXh6cTidsNht0Oh1kWTY9efJkFQA0NTX9MhaLtW3duhWPHj3CkydPEA6HEYvFEIvFehmG6QWAYDCYlUwmQdO0vb29fSdLCPlPUVFRZiQSQTAYRCgUWuiBeDyO4eHhnwG473a7JQA1Z86cObdjx469/f39uaFQiFZVtWf37t1H6+vrtXA4bK+trd2oKApYlsXjx49/zjIMM2i1Wj+UZRksywIAUnZht9sRCAR2er3e31ZXVycBYN++fd8C+PZlrd++fRuEEObkyZNfhkIhgRACTdOgqmo+7Xa7ByVJAk3TMJvNcDgcsFqtyMzMhF6vx+TkpLunp2fLu5qJEKI/e/bs152dnVt0Ot2CKaqqmsauX7/+dF9f33WGYYqj0WhRPB4vtNlsRU6nM9/hcOhlWcbo6GgjgG/eBj40NLSioaGh5cKFC2uLi4vBsiw4jkMikQCAZ9S9e/cKent7Py4sLLztcrkelpaW/ouiKMXr9TIAciRJKpyamiosKCg4V1VVJb44SMv169c3dXR07B0bG/sxx3F0X18fsrOz4Xa7EY1GEYvFwHHcRYoQQh08eHDo1KlTJRMTE+jv709OT0/7o9HoaDQa9SeTyaimaTJFUbaRkZG0sbGxoufPn5eIosgSQrB69WooioLe3l7YbDasWLECkiQhHo+jvLz8pyxFUaS1tfXzBw8enCwvLwdN04zf73cPDQ25fT4fpqamMD8/j2XLliEQCGBiYgKyLAMA3G43BEHA8PAwAEBVVSSTyZTNjDqdzi4aACoqKr7s6OiI0jQNnudht9vhcDhgMBjA8zwAQBAErFq1CsXFxXC5XPB4PMjNzUU4HEYgEABFUWAYBvF4HIqiIC8v73fNzc0a/SKTMCGkbXJyEmazGenp6XA6ndDr9UipIhKJgOd55ObmYsmSJSmFYWBgIJUxDAYDJEkCwzBdXq/3awCgU2qoqqr6Y3t7+8I1mZGRkbILMAyDZ8+eIRqNQhRFxGIxzM7OwufzIZFILJigy+WCyWSaPXDgQP2Cm6YGa9eu7X/48GGvLMsL5brdbrhcLmRnZ8NgMCAajSISiSAQCMDv9yOZTC7IdfHixRAEQdy+fftP9uzZM/EGAQBs2LDhdE9PD1RVhaqqC8ZnMpmgaRp8Ph/Gx8chiiIoigJFff8osdlsWLp06diuXbt+2NjYePdlzFcIamtrvZcvX56UJAmyLIOmaTx9+hSjo6OYmJhANBp9o9GcTmdizZo1p44cObKyrq5u8PX/rxBQFKUsWrToTyMjIwiFQohEIjCbzdA0DakHAQDQNA273U48Hs/VhoaGDzs7Oz/euHHj/BvsrxMAwJYtWz7v7u5WUsaXmZm5oO0XV6VcUFDw1f79+8vu3r27ubGxcfhtwKlgX58oLy//rq6u7oKiKDXT09MIBoOgKErhOO7G8uXLv6msrPzztm3bgjdu3HgX7v925W2Tly5dWnv+/Pm29PT0m7m5uV1lZWVXP/roo8h7Ib4W/wW5PFM4xqdwfQAAAABJRU5ErkJggg==', 'linkedin': 'iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAYAAACpSkzOAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAM6QAADOkBmiiHWwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJRSURBVEiJ7ZU/aCJREMa/t7soa5LOoGihktZOQSxSWykBIYVaWZ6NVa6wSZ/WI5BGziJypA1CQBLsgkKKgBjFQkEtkouJ+AdxdeeKnHvurXdcXK84uK/amfl4v9m3s++xbrdrury8PGm324dEZMYGxRj7arPZvoRCoSPh/Pz8pFqtftgkYEnmTqeT6PV6xDscjs9EZPpLIADAy8uLS5jP52bGGACA4ziEw2H4/X5IkoSrqytcX1/rBhHRrrCcCAaDCAQCShyJRPD6+oq7uzvdMG458Hg8GoPX69UN0YDG47HGsCqnG5TP50FESjyZTFAoFDYCYvF4nBbDAAB7e3vw+XyQJAnFYhGPj4+6IUQE4eekJEm4vb0F8DaFC1mtVphMb3+BLMtotVogItjtdjgcDhiNRvT7fTw8PKzcbhXI5XIhlUqpOkkkEpjP5zg+PoYg/LCfnp5if38fbrdbteB0OsXFxQVubm5+DTIYDKoiYww8z4OIwPO8qhaLxbCzs6Pp3GAwIBqN4vn5Gff390qe0zj/UKsgywqFQqpY843eo1KphHK5DLPZjIODAxiNRqXmdDqxvb2N4XCoD1Sv13F2dqbEs9kM0WhU5bFYLApo7a1bTOZClUpF49na2lKe1wb1ej1VvGqklwdobdB79R/0j4FkWdYYiEh1dawrAcATgF0AaDabyOVyyuE5HA4xmUwAAJlMRjl2ZFlGo9FQLTQajZDNZiGKouKp1WqL8hNLJpPpwWCQ0N3ybySKYpqLxWJHjLFP399s03riOC4dCAQ+fgMeouMzfwx22gAAAABJRU5ErkJggg==', 'RG': 'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAcCAYAAAB2+A+pAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMfwAADH8BdgxfmQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAM2SURBVEiJtZdLSytJFMd/1dXB+OiQRJEQBEnbPgISJGIQcePKjyBZzoP5AH6OuR9gFjPMznwC1650EbKSy00WPhJ8EMlDtG1M0p2axZCA1871cZM/NDRFnfqdqjrnVJUAODg4+E0IsQ8sA5LRyANKQogve3t7/4hcLvcH8NeIYL5SSv2uAftDHhSl1A/7CCH2dWBxWNBoNIppmgSDQarVKufn53ie59d1RQO0YUBjsRg7OztomkatVmNpaYnNzU2EEH7dNX0YUKUUpmlyd3dHPp9HKcXV1RXT09MIIXyXfihgKSWGYVCpVPoQ27axbXugjS/4HcHh29btdlFKsbq6SiwWA6BQKHB/f/82WEpJKpUiEAi8aA8EAiilaLVaNBoNrq+vabfbr+BCCG5vb3l8fCSTyaDr/ov6KrA8z6NcLtNqtUgkEszPz+M4Ds1mE9u2MQyDjY0Ndnd3mZmZ6ds4jkMoFAKg0Wjw8PCAEIJOp+ML9nWnZ5hIJJBSUiqV+gMIIbAsi3Q6zdbWFoeHh7iuS7lcZn19HcdxsG0by7Ko1+sD93lgcCml6Ha7SClftZ+dnbG4uIhhGMzOznJzc0OlUkHTNBYWFtB1nXq9zunp6aA8/lxUe57H09MThmEwPj7ed+ji4oLLy0uEEHieNyiHPw+WUjI5OYlS6lXE9krmj6DwyaplmiaGYVCtVqnX658Z4u0ZCyGIx+O0223GxsaYm5sjHo9Tq9U4OTn5FPRdYCkly8vLCCEIh8MopSgUCpTLZVzXHR3YdV2Ojo7wPI/t7W1isRjBYPCnoPDOPVZK4XlePz2SySThcHj04J4ajQbFYhEpJZlM5lWOjwwMUCwWaTabRCIR0un08MG9gt/778l1XfL5PJ1OB9M0WVlZGR54amoKy7IIBoPouo5lWYRCof7SNptN8vk83W6XVCrF2toaExMTHwKLXC734vCVUpJOp9F1/cW5rGkapVLpRcGIRqMkk0kikQiO43B8fMzz8/O7wd73Mx90EfArg0opNE178/LwnboaUPID+H2DnPkgFOCbppT68lGrn5VS6k8tm83+DfwKfOX/Z8ao5AFflVK/ZLPZf/8DudZq3wvXLmgAAAAASUVORK5CYII=', 'tweeter': 'iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAYAAACpSkzOAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMMQAADDEBLaRWDgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAK5SURBVEiJpZU7T+NAFEZP4kAePBwZ8TA0EUIRKKIgQhSImnZ/wDYr7Q/barddbRu2QVAQhChAgBQqQClwFEIcx8IYfLdKNk5sJ4GRRh6PPN+Z+90749jZ2VnGsqyfwD6QEREARISocdRcT7dF5AD4lmi327+AL0GCn4QgIhkR+SIiPxIish8k3i/yQVCn7ydEJD0sgjDBMUCZxCg2hQmqqsri4iKKotBoNKhWq741vesSvULpdJrJyUkajcZQy7a2tlheXqa3FQoFzs/PmZubQ9M0Dg8Pu2vivQJLS0sUi0Wy2WykFfl8fgACkEql2N3dJZfLcXFxgaqq/0G9O04mk8RiMba3t8nlcqHRrK6uDkB628TEBDs7O5imORgRgGVZ3Y/z+Tx7e3ssLCz4QMlkkng8HglqNpscHBzw9vbmz1EHVK1WWVtb6wpNTU1RLBZ5f3/HMAzq9TqO40RCAGq1Gq7r+jboK4aZmRmurq7Y3Nz0LVQUBV3X0XV9KATAcZwBy7vlLSJomjbU/1Ha8/PzAMhXdQ8PD5+GABiGEQ1qt9tcXl5+CvL09MTLy8ugdf0T9/f32LbNxsYGs7OzY4Our68DD/oASEQoFApMT0+PDTFNk7u7u0BQPAhULpdxXXds0PHxMZ7nDUBCQa1Wi1KpRKVSwTTNkSAnJyfU6/XQWz4QJCI4jsPj4yOKogyFnJ6ecnt7G3nTd3OUSCSYn59HURRUVUXXdTKZTCTAtm2Ojo585dwP6rx3Qa+vrzSbTdbX11lZWSEWi4UCLMvi5uaGSqWC53mh/67esa/qTNOkXC4DoGka2WyWVCoFgOu6tFotDMPAtu3QXISNA8tbRKjVaoEnPCwPYZZ1nnHP8+ww2Ed7P0RE7LjneX/7ff6ocES0pbiIfBWRP57n2aMAwywKGdsi8ltRlO//AFPkniYXwGRMAAAAAElFTkSuQmCC', 'udemy': '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', 'youtube': 'iVBORw0KGgoAAAANSUhEUgAAACEAAAAaCAYAAAA5WTUBAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMNwAADDcBracSlQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAKkSURBVEiJxZcxSBthFIC/918uGhxMsyptcGjoIgGHW9wSihQKGZrNthHsIC7S1TqWgkRwcZV2lKo0FouixaEuEQ4khIIdrClkEoIZgiae93fQgFgll5jqt93x3v++e3f/3TvhGgYHBx/UarUUEAMeA48A/3WxDagBf4A9EdmsVqsfd3d3j64GyeWDZDJpFAqFKWAC6G6haCPKIjKTzWbfA+4/Ev39/V2dnZ3LwNP/UPwqaycnJy9yuVwFQF2cVIFA4PMdCQAMBQKBL8lk0gAwACzLmtJav7kjgTp95XK5ViwWf0g0Gg36/f7fQLBRltYaEWkU5hkRKTmO06dM03ztRaAuEQ6H0Vq3RUJrHTIM46XR29v7jvNt2BClFEtLS0QiEfb39ymVSrfujIg4Cog0mxiPx1lYWGBycpKenh5c122cdANa64gCHra6QCKRYHl5mfHxcYLBII7jtLJMWAEdrUrUSaVSrK6uMjo6SigU4uzsrJn0DtU4xhs+n4+xsTFWVlYYHh6mq6vL821qm0Qd0zSZmJggk8kQi8XuR6LO1tYW+XzeUzd87S6ey+WYnZ0ln88jIijV+DrbJnF4eMj09DTb29u4rtvU+8MHVLnFDjk+PiadTrO+vs7p6WkrS1R9QAGPb8zLaK2Zm5tjcXGRSqXiqe03sO8D9pqVyGQyzM/PUywWMQzjNgIAv3xa600Ree4l2nEcRkZGODg4QCmFYRi3KQ6AiGzIwMBAt2EYB9znp9y27bLWesZjUtsELkjbtl2ur6osy/qqtX7W7io3ISIb2Wx2CHDrT5TrOE4SWLsjgW+O4yS4mLiv9ldZljWptX6Lx2mrSY6A9M7OzgeuG/kvE41Gg6ZpvhKROPCE85mj5Z8fEfnpuu5313U/2bZdvhr0F9Fo9phaoDu9AAAAAElFTkSuQmCC'}
        footer = '''<div align="right">
                      <p align="right"><b>'''+self.tr('Author: Leandro Franca', 'Autor: Leandro França')+'''</b></p>
                      <div align="right">
                      <a target="_blank" rel="noopener noreferrer" href="https://www.udemy.com/user/leandro-luiz-silva-de-franca/"><img title="Udemy" src="data:image/png;base64,'''+dic_BW['udemy']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/GEOCAPT/"><img title="Facebook" src="data:image/png;base64,'''+dic_BW['face']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.youtube.com/channel/UCLrewDGciytcBG9r0OxTW2w"><img title="Youtube" src="data:image/png;base64,'''+dic_BW['youtube']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.researchgate.net/profile/Leandro_Franca2"><img title="ResearchGate" src="data:image/png;base64,'''+dic_BW['RG']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://github.com/LEOXINGU"><img title="GitHub" src="data:image/png;base64,'''+dic_BW['github']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.linkedin.com/in/leandro-fran%C3%A7a-93093714b/"><img title="Linkedin" src="data:image/png;base64,'''+dic_BW['linkedin']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="http://lattes.cnpq.br/8559852745183879"><img title="Lattes" src="data:image/png;base64,'''+dic_BW['lattes']+'''"></a>
                      </div>
                    </div>'''
        if self.LOC == 'pt':
            return txt_pt + footer
        else:
            return self.tr(txt_en) + footer
    
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
        
        codigo = self.parameterAsString(parameters,
                                                     self.CODIGO,
                                                     context)
        
        if vertice is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.PONTOREF))
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
        
        expr = QgsExpression( "\"codigo\"='{}'".format( codigo ) )
        pnt = False
        for feat in vertice.getFeatures(QgsFeatureRequest( expr )):
            pnt = feat.geometry().asMultiPoint()[0]
            ponto = feat
            break
        
        # Verificando se o código do marco é válido
        if not pnt:
            erro_txt = self.tr('The survey mark code {} is not valid!'.format(codigo), 'O código do marco {} não é válido!'.format(codigo))
            raise QgsProcessingException(erro_txt)
        
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
                '[NI]':  self.str2HTML(ponto['imóvel']),
                '[MUN]': self.str2HTML(ponto['município']),
                '[UF]':  self.str2HTML(ponto['UF']),
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
                '[REP_TEC]':  self.str2HTML(ponto['Resp_Tecnico']),
                '[CREA]': self.str2HTML(ponto['CREA']),
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