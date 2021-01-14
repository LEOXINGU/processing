# -*- coding: utf-8 -*-

"""
mosaicRaster.py
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
__date__ = '2021-01-12'
__copyright__ = '(C) 2021, Leandro França'

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsWkbTypes,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsPointXY,
                       QgsGeometry,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterField,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterEnum,
                       QgsFeatureRequest,
                       QgsExpression,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsApplication,
                       QgsProject,
                       QgsRasterLayer,
                       QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem)
import gdal
from osgeo import osr, gdal_array
from itertools import combinations
from matplotlib import path
import numpy as np
from pyproj.crs import CRS
from math import floor, ceil

class MosaicRaster(QgsProcessingAlgorithm):

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
        return MosaicRaster()

    def name(self):
        return 'mosaicraster'

    def displayName(self):
        return self.tr('Mosaic Raster', 'Mosaicar Raster')

    def group(self):
        return self.tr('LF Raster')

    def groupId(self):
        return 'lf_raster'
    
    def tags(self):
        return self.tr('mosaic,merge,raster,combine,mosaik,mosaico,mesclar').split(',')
    
    def shortHelpString(self):
        txt_en = 'Creates raster mosaic: a combination or merge of two or more images.'
        txt_pt = 'Cria um mosaico: uma combinação ou mesclagem de duas ou mais imagens.'
        dic_BW = {'face': 'iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMMwAADDMBUlqVhwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAIUSURBVEiJvZa9quJAGIbfMfEYTUSUQAqLYOnehJobsBTlHLbRQtKKlY3lObegxRa7pRdg7y0saiuoKAErMZif2Squ2eTEOCfsC1Pk+3uYb2YyQwCg1+u9UUqHAKoAOCQrB8ASwPt0Ov1JdF3/bprmj4QhoXp5eXnjTdMcUEr/Bw+WZQ15Smn1q4UIIZBlGaIoghBys2+3W1yv19u367rfeAAc6ww5jkOz2USj0YAoigH/aDTCbrfzpfCUUrAC2+02NE2LjPm3NjNQkiTU6/WHsFAgi1RVRSqVCthd171BwmozA/P5fMA2n88xm81g2zYAwHGccCAL9H43elosFrhcLpE5zMCwHMdxImtRSp8DptNpZDIZAIAgCAG/IAi+42Ga5q29nkin06FxgZqmodvtxooFgPF4jPV67bM9NcNnW384HJI7h49kWRZOp9PXgOfzGfv9HgCQy+VQKBR8fsMwYFkWAOB4PMJ13UAN0mq1Yq/hfVytVoOu6z7/YDDAZrP5Wzzk6CR6LOLEJLqGcWrxYX2OW5wJmOQOjQX0ApOERgIrlQoTUJblgK1cLodeWZ4IIeDDngZx5P1T75XNZiFJUmQeTyl1wPAW/awrD7rlpDiOW3qL/cz4DBY1CCG/U4qifDw7O1YpivJBAGAymbwahjG0bbtKKeXjJJdKJaiq6rOtVqvAjU8IsTmOWxaLxfd+v//rD1H2cZ8dKhk8AAAAAElFTkSuQmCC', 'github': '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', 'instagram': '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', 'lattes': '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', 'linkedin': 'iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAYAAACpSkzOAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAM6QAADOkBmiiHWwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJRSURBVEiJ7ZU/aCJREMa/t7soa5LOoGihktZOQSxSWykBIYVaWZ6NVa6wSZ/WI5BGziJypA1CQBLsgkKKgBjFQkEtkouJ+AdxdeeKnHvurXdcXK84uK/amfl4v9m3s++xbrdrury8PGm324dEZMYGxRj7arPZvoRCoSPh/Pz8pFqtftgkYEnmTqeT6PV6xDscjs9EZPpLIADAy8uLS5jP52bGGACA4ziEw2H4/X5IkoSrqytcX1/rBhHRrrCcCAaDCAQCShyJRPD6+oq7uzvdMG458Hg8GoPX69UN0YDG47HGsCqnG5TP50FESjyZTFAoFDYCYvF4nBbDAAB7e3vw+XyQJAnFYhGPj4+6IUQE4eekJEm4vb0F8DaFC1mtVphMb3+BLMtotVogItjtdjgcDhiNRvT7fTw8PKzcbhXI5XIhlUqpOkkkEpjP5zg+PoYg/LCfnp5if38fbrdbteB0OsXFxQVubm5+DTIYDKoiYww8z4OIwPO8qhaLxbCzs6Pp3GAwIBqN4vn5Gff390qe0zj/UKsgywqFQqpY843eo1KphHK5DLPZjIODAxiNRqXmdDqxvb2N4XCoD1Sv13F2dqbEs9kM0WhU5bFYLApo7a1bTOZClUpF49na2lKe1wb1ej1VvGqklwdobdB79R/0j4FkWdYYiEh1dawrAcATgF0AaDabyOVyyuE5HA4xmUwAAJlMRjl2ZFlGo9FQLTQajZDNZiGKouKp1WqL8hNLJpPpwWCQ0N3ybySKYpqLxWJHjLFP399s03riOC4dCAQ+fgMeouMzfwx22gAAAABJRU5ErkJggg==', 'RG': 'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAcCAYAAAB2+A+pAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMfwAADH8BdgxfmQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAM2SURBVEiJtZdLSytJFMd/1dXB+OiQRJEQBEnbPgISJGIQcePKjyBZzoP5AH6OuR9gFjPMznwC1650EbKSy00WPhJ8EMlDtG1M0p2axZCA1871cZM/NDRFnfqdqjrnVJUAODg4+E0IsQ8sA5LRyANKQogve3t7/4hcLvcH8NeIYL5SSv2uAftDHhSl1A/7CCH2dWBxWNBoNIppmgSDQarVKufn53ie59d1RQO0YUBjsRg7OztomkatVmNpaYnNzU2EEH7dNX0YUKUUpmlyd3dHPp9HKcXV1RXT09MIIXyXfihgKSWGYVCpVPoQ27axbXugjS/4HcHh29btdlFKsbq6SiwWA6BQKHB/f/82WEpJKpUiEAi8aA8EAiilaLVaNBoNrq+vabfbr+BCCG5vb3l8fCSTyaDr/ov6KrA8z6NcLtNqtUgkEszPz+M4Ds1mE9u2MQyDjY0Ndnd3mZmZ6ds4jkMoFAKg0Wjw8PCAEIJOp+ML9nWnZ5hIJJBSUiqV+gMIIbAsi3Q6zdbWFoeHh7iuS7lcZn19HcdxsG0by7Ko1+sD93lgcCml6Ha7SClftZ+dnbG4uIhhGMzOznJzc0OlUkHTNBYWFtB1nXq9zunp6aA8/lxUe57H09MThmEwPj7ed+ji4oLLy0uEEHieNyiHPw+WUjI5OYlS6lXE9krmj6DwyaplmiaGYVCtVqnX658Z4u0ZCyGIx+O0223GxsaYm5sjHo9Tq9U4OTn5FPRdYCkly8vLCCEIh8MopSgUCpTLZVzXHR3YdV2Ojo7wPI/t7W1isRjBYPCnoPDOPVZK4XlePz2SySThcHj04J4ajQbFYhEpJZlM5lWOjwwMUCwWaTabRCIR0un08MG9gt/778l1XfL5PJ1OB9M0WVlZGR54amoKy7IIBoPouo5lWYRCof7SNptN8vk83W6XVCrF2toaExMTHwKLXC734vCVUpJOp9F1/cW5rGkapVLpRcGIRqMkk0kikQiO43B8fMzz8/O7wd73Mx90EfArg0opNE178/LwnboaUPID+H2DnPkgFOCbppT68lGrn5VS6k8tm83+DfwKfOX/Z8ao5AFflVK/ZLPZf/8DudZq3wvXLmgAAAAASUVORK5CYII=', 'tweeter': 'iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAYAAACpSkzOAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMMQAADDEBLaRWDgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAK5SURBVEiJpZU7T+NAFEZP4kAePBwZ8TA0EUIRKKIgQhSImnZ/wDYr7Q/barddbRu2QVAQhChAgBQqQClwFEIcx8IYfLdKNk5sJ4GRRh6PPN+Z+90749jZ2VnGsqyfwD6QEREARISocdRcT7dF5AD4lmi327+AL0GCn4QgIhkR+SIiPxIish8k3i/yQVCn7ydEJD0sgjDBMUCZxCg2hQmqqsri4iKKotBoNKhWq741vesSvULpdJrJyUkajcZQy7a2tlheXqa3FQoFzs/PmZubQ9M0Dg8Pu2vivQJLS0sUi0Wy2WykFfl8fgACkEql2N3dJZfLcXFxgaqq/0G9O04mk8RiMba3t8nlcqHRrK6uDkB628TEBDs7O5imORgRgGVZ3Y/z+Tx7e3ssLCz4QMlkkng8HglqNpscHBzw9vbmz1EHVK1WWVtb6wpNTU1RLBZ5f3/HMAzq9TqO40RCAGq1Gq7r+jboK4aZmRmurq7Y3Nz0LVQUBV3X0XV9KATAcZwBy7vlLSJomjbU/1Ha8/PzAMhXdQ8PD5+GABiGEQ1qt9tcXl5+CvL09MTLy8ugdf0T9/f32LbNxsYGs7OzY4Our68DD/oASEQoFApMT0+PDTFNk7u7u0BQPAhULpdxXXds0PHxMZ7nDUBCQa1Wi1KpRKVSwTTNkSAnJyfU6/XQWz4QJCI4jsPj4yOKogyFnJ6ecnt7G3nTd3OUSCSYn59HURRUVUXXdTKZTCTAtm2Ojo585dwP6rx3Qa+vrzSbTdbX11lZWSEWi4UCLMvi5uaGSqWC53mh/67esa/qTNOkXC4DoGka2WyWVCoFgOu6tFotDMPAtu3QXISNA8tbRKjVaoEnPCwPYZZ1nnHP8+ww2Ed7P0RE7LjneX/7ff6ocES0pbiIfBWRP57n2aMAwywKGdsi8ltRlO//AFPkniYXwGRMAAAAAElFTkSuQmCC', 'udemy': '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', 'youtube': 'iVBORw0KGgoAAAANSUhEUgAAACEAAAAaCAYAAAA5WTUBAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMNwAADDcBracSlQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAKkSURBVEiJxZcxSBthFIC/918uGhxMsyptcGjoIgGHW9wSihQKGZrNthHsIC7S1TqWgkRwcZV2lKo0FouixaEuEQ4khIIdrClkEoIZgiae93fQgFgll5jqt93x3v++e3f/3TvhGgYHBx/UarUUEAMeA48A/3WxDagBf4A9EdmsVqsfd3d3j64GyeWDZDJpFAqFKWAC6G6haCPKIjKTzWbfA+4/Ev39/V2dnZ3LwNP/UPwqaycnJy9yuVwFQF2cVIFA4PMdCQAMBQKBL8lk0gAwACzLmtJav7kjgTp95XK5ViwWf0g0Gg36/f7fQLBRltYaEWkU5hkRKTmO06dM03ztRaAuEQ6H0Vq3RUJrHTIM46XR29v7jvNt2BClFEtLS0QiEfb39ymVSrfujIg4Cog0mxiPx1lYWGBycpKenh5c122cdANa64gCHra6QCKRYHl5mfHxcYLBII7jtLJMWAEdrUrUSaVSrK6uMjo6SigU4uzsrJn0DtU4xhs+n4+xsTFWVlYYHh6mq6vL821qm0Qd0zSZmJggk8kQi8XuR6LO1tYW+XzeUzd87S6ey+WYnZ0ln88jIijV+DrbJnF4eMj09DTb29u4rtvU+8MHVLnFDjk+PiadTrO+vs7p6WkrS1R9QAGPb8zLaK2Zm5tjcXGRSqXiqe03sO8D9pqVyGQyzM/PUywWMQzjNgIAv3xa600Ree4l2nEcRkZGODg4QCmFYRi3KQ6AiGzIwMBAt2EYB9znp9y27bLWesZjUtsELkjbtl2ur6osy/qqtX7W7io3ISIb2Wx2CHDrT5TrOE4SWLsjgW+O4yS4mLiv9ldZljWptX6Lx2mrSY6A9M7OzgeuG/kvE41Gg6ZpvhKROPCE85mj5Z8fEfnpuu5313U/2bZdvhr0F9Fo9phaoDu9AAAAAElFTkSuQmCC'}
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
    
    RASTERLIST ='RASTERLIST'
    CHANGERESOLUTION = 'CHANGERESOLUTION'
    RESOLUTION = 'RESOLUTION'
    OVERLAP = 'OVERLAP'
    NULLVALUE = 'NULLVALUE'
    RESAMPLING = 'RESAMPLING'
    MOSAIC = 'MOSAIC'
    OPEN = 'OPEN'
    
    def initAlgorithm(self, config=None):
        # INPUT
        self.addParameter(
            QgsProcessingParameterMultipleLayers(
                self.RASTERLIST,
                self.tr('Raster List', 'Lista de Rasters'),
                layerType = QgsProcessing.TypeRaster
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CHANGERESOLUTION,
                self.tr('Change resolution', 'Alterar resolução'),
                defaultValue = False
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.RESOLUTION,
                self.tr('New Resolution', 'Nova resolução espacial'),
                type =1, #Double = 1 and Integer = 0
                defaultValue = 100,
                optional = True
            )
        )
        
        sobrep = [self.tr('First (faster)', 'Primeiro (mais rápido)'),
                 self.tr('Average', 'Média'),
                 self.tr('Median', 'Mediana'),
                 self.tr('Maximum', 'Máximo'),
                 self.tr('Minimum', 'Mínimo')]
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OVERLAP,
                self.tr('Ovelap', 'Sobreposição'),
				options = sobrep,
                defaultValue= 0
            )
        )
        
        interp = [self.tr('Nearest neighbor', 'Vizinho mais próximo'),
                 self.tr('Bilinear'),
                 self.tr('Bicubic', 'Bicúbica')]
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.RESAMPLING,
                self.tr('Interpolation', 'Interpolação'),
				options = interp,
                defaultValue= 0
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NULLVALUE,
                self.tr('Null value', 'Valor nulo'),
                type =0, #Double = 1 and Integer = 0
                defaultValue = 0
            )
        )
        
        # OUTPUT
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.MOSAIC,
                self.tr('Mosaic', 'Mosaico'),
                fileFilter = '.tif'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OPEN,
                self.tr('Load mosaic', 'Carregar mosaico'),
                defaultValue= True
            )
        )
    
    # Função de Interpolação
    def Interpolar(self, X, Y, BAND, origem, resol_X, resol_Y, metodo, nulo):
        if metodo == 'nearest':
            linha = int(round((origem[1]-Y)/resol_Y - 0.5))
            coluna = int(round((X - origem[0])/resol_X - 0.5))
            if BAND[linha][coluna] != nulo:
                return float(BAND[linha][coluna])
            else:
                return nulo
        elif metodo == 'bilinear':
            nlin = len(BAND)
            ncol = len(BAND[0])
            I = (origem[1]-Y)/resol_Y - 0.5
            J = (X - origem[0])/resol_X - 0.5
            di = I - floor(I)
            dj = J - floor(J)
            if I<0:
                I=0
            if I>nlin-1:
                I=nlin-1
            if J<0:
                J=0
            if J>ncol-1:
                J=ncol-1
            if (BAND[int(floor(I)):int(ceil(I))+1, int(floor(J)):int(ceil(J))+1] == nulo).sum() == 0:
                Z = (1-di)*(1-dj)*BAND[int(floor(I))][int(floor(J))] + (1-dj)*di*BAND[int(ceil(I))][int(floor(J))] + (1-di)*dj*BAND[int(floor(I))][int(ceil(J))] + di*dj*BAND[int(ceil(I))][int(ceil(J))]
                return float(Z)
            else:
                return nulo
        elif metodo == 'bicubic':
            nlin = len(BAND)
            ncol = len(BAND[0])
            I = (origem[1]-Y)/resol_Y - 0.5
            J = (X - origem[0])/resol_X - 0.5
            di = I - floor(I)
            dj = J - floor(J)
            I=int(floor(I))
            J=int(floor(J))
            if I<2:
                I=2
            if I>nlin-3:
                I=nlin-3
            if J<2:
                J=2
            if J>ncol-3:
                J=ncol-3
            if (BAND[I-1:I+3, J-1:J+3] == nulo).sum() == 0:
                MatrInv = (np.mat([[-1, 1, -1, 1], [0, 0, 0, 1], [1, 1, 1, 1], [8, 4, 2, 1]])).I # < Jogar para fora da funcao
                MAT  = np.mat([[BAND[I-1, J-1],   BAND[I-1, J],   BAND[I-1, J+1],  BAND[I-2, J+2]],
                                [BAND[I, J-1],      BAND[I, J],      BAND[I, J+1],      BAND[I, J+2]],
                                [BAND[I+1, J-1],  BAND[I+1, J], BAND[I+1, J+1], BAND[I+1, J+2]],
                                [BAND[I+2, J-1],  BAND[I+2, J], BAND[I+2, J+1], BAND[I+2, J+2]]])
                coef = MatrInv*MAT.transpose()
                # Horizontal
                pi = coef[0,:]*pow(dj,3)+coef[1,:]*pow(dj,2)+coef[2,:]*dj+coef[3,:]
                # Vertical
                coef2 = MatrInv*pi.transpose()
                pj = coef2[0]*pow(di,3)+coef2[1]*pow(di,2)+coef2[2]*di+coef2[3]
                return float(pj)
            else:
                return nulo
    
    def processAlgorithm(self, parameters, context, feedback):
        
        # inputs
        rasters = self.parameterAsLayerList(
            parameters,
            self.RASTERLIST,
            context
        )
        if rasters is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.RASTERLIST))
        
        reamostragem = self.parameterAsEnum(
            parameters,
            self.RESAMPLING,
            context
        )
        reamostragem = ['nearest','bilinear','bicubic'][reamostragem]
        
        sobrep = self.parameterAsEnum(
            parameters,
            self.OVERLAP,
            context
        )
        
        muda_res = self.parameterAsBool( 
            parameters,
            self.CHANGERESOLUTION,
            context
        )
        
        resolucao = self.parameterAsDouble( 
            parameters,
            self.RESOLUTION,
            context
        )
        
        valor_nulo = self.parameterAsDouble( 
            parameters,
            self.NULLVALUE,
            context
        )
        
        # output
        
        Output = self.parameterAsFileOutput( 
            parameters,
            self.MOSAIC,
            context
        )
        
        Carregar = self.parameterAsBool( 
            parameters,
            self.OPEN,
            context
        )
        
        
        lista = []
        for raster_lyr in rasters:
            lista += [raster_lyr.dataProvider().dataSourceUri()]
        if len(lista) < 2:
            raise QgsProcessingException(self.tr('The number of input raster must be more than 1!', 'O número de rasters deve ser maior que 1!'))
        
        # Gerar geometria para cada raster
        geoms = []
        SRC = []
        n_bands =[]
        GDT = []
        XRES, YRES = [], []
        for item in lista:
            image = gdal.Open(item)
            SRC += [image.GetProjection()] # wkt
            ulx, xres, xskew, uly, yskew, yres  = image.GetGeoTransform()
            cols = image.RasterXSize
            rows = image.RasterYSize
            n_bands += [image.RasterCount]
            GDT += [image.GetRasterBand(1).DataType]
            XRES += [xres]
            YRES += [yres]
            image=None # Close image
            # Creating BBox
            coord = [[QgsPointXY(ulx, uly),
                      QgsPointXY(ulx+cols*xres, uly),
                      QgsPointXY(ulx+cols*xres, uly+rows*yres),
                      QgsPointXY(ulx, uly+rows*yres),
                      QgsPointXY(ulx, uly)]]
            geom = QgsGeometry.fromPolygonXY(coord)
            geoms += [geom]

        ## Validar dados de entrada
        # Mesmo numero de bandas
        if not n_bands.count(n_bands[0]) == len(n_bands):
            raise QgsProcessingException(self.tr('The images must have the same number of bands!', 'As imagens devem ter o mesmo número de bandas!'))
        # Mesmo SRC
        if not SRC.count(SRC[0]) == len(SRC):
            raise QgsProcessingException(self.tr('The images must have the same CRS!', 'As imagens devem ter o mesmo SRC!'))
        # Mesmo GDT
        if not GDT.count(GDT[0]) == len(GDT):
            raise QgsProcessingException(self.tr('The images must have the same data type!', 'As imagens devem ter o tipo de dado!'))
        
        # Dados para o raster de saída
        prj = SRC[0]
        n_bands = n_bands[0]
        GDT = GDT[0]
        xres = np.mean(XRES)
        yres = np.mean(YRES)

        # Mesclar geometrias e obter a extensão
        new_geom = QgsGeometry()
        new_geom = new_geom.unaryUnion(geoms)
        extensao = new_geom.boundingBox()

        # Coodenadas máxima e mínima da extensão
        y_min = extensao.yMinimum()
        y_max = extensao.yMaximum()
        x_min = extensao.xMinimum()
        x_max = extensao.xMaximum()

        # Transformar resolucao de metros para graus, se o SRC for Geográfico
        src_qgis = QgsCoordinateReferenceSystem(prj)
        if src_qgis.isGeographic():
            EPSG = int(src_qgis.authid().split(':')[-1])
            proj_crs = CRS.from_epsg(EPSG)
            a=proj_crs.ellipsoid.semi_major_metre
            f=1/proj_crs.ellipsoid.inverse_flattening
            e2 = f*(2-f)
            N = a/np.sqrt(1-e2*(np.sin((y_min+y_max)/2))**2) # Raio de curvatura 1º vertical
            M = a*(1-e2)/(1-e2*(np.sin((y_min+y_max)/2))**2)**(3/2.) # Raio de curvatura meridiana
            R = np.sqrt(M*N) # Raio médio de Gauss
            resolucao /= R

        # Definir n_col, n_lin e resolucao
        if muda_res:
            n_lin = round((y_max-y_min)/abs(resolucao))
            n_col = round((x_max-x_min)/abs(resolucao))
            xres = resolucao
            yres = -resolucao
        else:
            n_lin = round((y_max-y_min)/abs(yres))
            n_col = round((x_max-x_min)/abs(xres))
            xres = (x_max-x_min)/n_col
            yres = -(y_max-y_min)/n_lin

        # Geotransform do Mosaico
        ulx = x_min
        uly = y_max
        xskew, yskew = 0, 0
        geotransform = [ulx, xres, xskew, uly, yskew, yres]
        origem = (ulx, uly)
        resol_X = abs(xres)
        resol_Y = abs(yres)
    

        # Numeração das Imagens
        valores = list(range(1,len(lista)+1))

        # Definição de áreas de varredura
        feedback.pushInfo(self.tr('Defining mosaic filling areas...', 'Definindo áreas de preenchimento do mosaico...'))
        if sobrep != 0:
        # Gerar combinações dos Rasters
            combs = []
            for k in valores:
                combs += list(combinations(valores,k))

            # Armazenar geometrias exclusivas de cada combinação
            classes = {}
            for comb in combs:
                if len(comb)==1:
                    geom1 = geoms[comb[0]-1]
                    lista_outras = []
                    for geom in geoms:
                        if geom1 != geom:
                            lista_outras += [geom]
                    outras = QgsGeometry()
                    outras = outras.unaryUnion(lista_outras)
                    diferença = geom1.difference(outras)
                    if not diferença.isEmpty():
                        classes[comb] = {'geom': diferença}
                elif len(comb) < len(valores):
                    intersecao = geoms[comb[0]-1]
                    sentinela = True
                    for ind in comb[1:]:
                        geom = geoms[ind-1]
                        if geom.intersects(intersecao):
                            intersecao = intersecao.intersection(geom)
                        else:
                            sentinela = False
                            continue
                    lista_outras = []
                    for valor in valores:
                        if valor not in comb:
                            lista_outras += [geoms[valor-1]]
                    outras = QgsGeometry()
                    outras = outras.unaryUnion(lista_outras)
                    if sentinela:
                        diferença = intersecao.difference(outras)
                        if not diferença.isEmpty():
                            classes[comb] = {'geom': diferença}
                else:
                    intersecao = geoms[comb[0]-1]
                    sentinela = True
                    for ind in comb[1:]:
                        geom = geoms[ind-1]
                        if geom.intersects(intersecao):
                            intersecao = intersecao.intersection(geom)
                        else:
                            sentinela = False
                            continue
                    if sentinela:
                        classes[comb] = {'geom': intersecao}
        else:
            # Gerar geometrias por área sem cálculo de sobreposição ("first")
            combs = np.array(valores)[:,np.newaxis]
            classes = {}
            acumulado = geoms[combs[0][0]-1]
            classes[(1,)] = {'geom': acumulado}
            for k in range(1, len(combs)):
                comb = combs[k]
                geom = geoms[comb[0]-1]
                diferenca = geom.difference(acumulado)
                classes[(comb[0],)] = {'geom': diferenca}
                acumulado = acumulado.combine(geom)

        # Gerar lista com os valores classificados
        Percent = 100.0/(len(classes))
        current = 0
        for classe in classes:
            feedback.pushInfo((self.tr('Classifying class {}...', 'Classificando classe {}...')).format(str(classe)))
            geom = classes[classe]['geom']
            coords = geom.asPolygon()[0]
            caminho = []
            for ponto in coords:
                linha = (origem[1]-ponto.y())/resol_Y
                coluna = (ponto.x() - origem[0])/resol_X
                caminho += [(linha, coluna)]
            p = path.Path(caminho)
            box = geom.boundingBox()
            uly = box.yMaximum()
            lry = box.yMinimum()
            ulx = box.xMinimum()
            lrx = box.xMaximum()
            # Limites de Varredura
            row_ini = int(round((origem[1]-uly)/resol_Y - 0.5))-1
            row_fim = int(round((origem[1]-lry)/resol_Y - 0.5))+1
            col_ini = int(round((ulx - origem[0])/resol_X - 0.5))-1
            col_fim = int(round((lrx - origem[0])/resol_X - 0.5))+1
            lin, col = np.meshgrid(np.arange(row_ini, row_fim),np.arange(col_ini, col_fim))
            LIN = lin.flatten()[:,np.newaxis] + 0.5 # centro do pixel
            COL = col.flatten()[:,np.newaxis] + 0.5
            pixels_center = np.hstack((LIN, COL))
            # Verificando pixels dentro de poligono
            flags = p.contains_points(pixels_center)
            pixels_x = LIN.flatten()*flags
            pixels_y = COL.flatten()*flags
            pixels_x = (pixels_x[pixels_x>0] - 0.5).astype('int')[:,np.newaxis]
            pixels_y = (pixels_y[pixels_y>0] - 0.5).astype('int')[:,np.newaxis]
            pixels = np.hstack((pixels_x, pixels_y))
            classes[classe]['pixels'] = pixels
            current += 1
            feedback.setProgress(int(current * Percent))

        # Criar Raster
        Driver = gdal.GetDriverByName('GTiff').Create(Output, n_col, n_lin, n_bands, GDT)
        Driver.SetGeoTransform(geotransform)
        Driver.SetProjection(prj)


        # Mosaicar por banda
        Percent = 100.0/(n_lin*n_col*n_bands)
        current = 0
        
        for k in range(n_bands):
            feedback.pushInfo((self.tr('Creating band {}...', 'Criando banda {}...')).format(str(k+1)))
            # Criar Array do mosaico
            tipo = gdal_array.GDALTypeCodeToNumericTypeCode(GDT)
            banda = np.ones((n_lin,n_col), dtype = tipo) * valor_nulo
            inteiro = True if GDT in (gdal.GDT_Byte, 
                                      gdal.GDT_UInt16, 
                                      gdal.GDT_Int16,
                                      gdal.GDT_UInt32,
                                      gdal.GDT_Int32) else False
            
            # Para cada classe abrir banda da(s) imagem(ns)
            for classe in classes:
                imgs = {}
                for img in classe:
                    img_path = lista[img-1]
                    image = gdal.Open(img_path)
                    ulx, xres, xskew, uly, yskew, yres  = image.GetGeoTransform()
                    img_origem = (ulx, uly)
                    img_resol_X = abs(xres)
                    img_resol_Y = abs(yres)
                    img_band = image.GetRasterBand(k+1).ReadAsArray()
                    imgs[img] = {'band': img_band,
                                 'xres': img_resol_X,
                                 'yres': img_resol_Y,
                                 'origem': img_origem }
                    image = None
                                
                if sobrep == 0: # Se for "primeiro", interpolar apenas da primeira img da comb, caso contrário
                    img = classe[0]
                    # Para cada pixel da classe
                    for px in classes[classe]['pixels']:
                        lin,col = px
                        X = origem[0] + resol_X*(col + 0.5)
                        Y = origem[1] - resol_Y*(lin + 0.5)
                        Interpolado = self.Interpolar(X, Y, 
                                                 imgs[img]['band'],
                                                 imgs[img]['origem'],
                                                 imgs[img]['xres'],
                                                 imgs[img]['yres'],
                                                 reamostragem,
                                                 valor_nulo)
                        if Interpolado != valor_nulo:
                            banda[lin][col] = round(Interpolado) if inteiro else Interpolado
                        
                        if feedback.isCanceled():
                            break
                        current += 1
                        feedback.setProgress(int(current * Percent))
                
                else: # Para cada pixel da classe interpolar o valor da banda de cada img
                    for px in classes[classe]['pixels']:
                        lin,col = px
                        X = origem[0] + resol_X*(col + 0.5)
                        Y = origem[1] - resol_Y*(lin + 0.5)
                        interp_values = []
                        for img in imgs:
                            Interpolado = self.Interpolar(X, Y, 
                                                     imgs[img]['band'],
                                                     imgs[img]['origem'],
                                                     imgs[img]['xres'],
                                                     imgs[img]['yres'],
                                                     reamostragem,
                                                     valor_nulo)
                            if Interpolado != valor_nulo:
                                interp_values += [Interpolado]
                        # Calcular o valor agregado (0:first, 1:average, 2:median, 3:min, 4:max) e inserir na banda (se byte, arredondar)
                        if interp_values:
                            if sobrep == 1:
                                result = np.mean(interp_values)
                            elif sobrep == 2:
                                result = np.median(interp_values)
                            elif sobrep == 3:
                                result = np.min(interp_values)
                            elif sobrep == 4:
                                result = np.max(interp_values)
                            banda[lin][col] = round(result) if inteiro else result
                        
                        if feedback.isCanceled():
                            break
                        current += 1
                        feedback.setProgress(int(current * Percent))

            # Salvar banda
            outband = Driver.GetRasterBand(k+1)
            feedback.pushInfo(self.tr('Writing Band {}...'.format(k+1), 'Escrevendo Banda {}...'.format(k+1)))
            outband.WriteArray(banda)
            outband.SetNoDataValue(valor_nulo)

        # Salvar e Fechar Raster
        Driver.FlushCache()   # Escrever no disco
        Driver = None   # Salvar e fechar
        
        
        feedback.pushInfo(self.tr('Operation completed successfully!', 'Operação finalizada com sucesso!'))
        feedback.pushInfo('Leandro França - Eng Cart')
        self.CAMINHO = Output
        self.CARREGAR = Carregar
        return {self.MOSAIC: Output}
    
    # Carregamento de arquivo de saída
    def postProcessAlgorithm(self, context, feedback):
        if self.CARREGAR:
            rlayer = QgsRasterLayer(self.CAMINHO, self.tr('Mosaic', 'Mosaico'))
            QgsProject.instance().addMapLayer(rlayer)
        return {}