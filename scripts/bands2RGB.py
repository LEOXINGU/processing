# -*- coding: utf-8 -*-

"""
bands2RGB.py
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
__date__ = '2020-08-23'
__copyright__ = '(C) 2020, Leandro França'

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
                       QgsProcessingParameterField,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterEnum,
                       QgsFeatureRequest,
                       QgsExpression,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterRasterDestination,
                       QgsApplication,
                       QgsProject,
                       QgsRasterLayer,
                       QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem)
import processing
import gdal
from osgeo import osr, gdal_array

class Bands2RGB(QgsProcessingAlgorithm):

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
        return Bands2RGB()

    def name(self):
        return 'bands2rgb'

    def displayName(self):
        return self.tr('RGB Composite', 'Composição RGB')

    def group(self):
        return self.tr('LF Raster')

    def groupId(self):
        return 'lf_raster'

    def shortHelpString(self):
        if self.LOC == 'pt':
            return "Realiza a cominação de três bandas em uma única imagem, apresentando-as nas bandas vermelha (R), verde (G) e Azul (B)."
        else:
            return self.tr("Combine three image bands into one picture by display each band as either Red, Green or Blue.")
    
    R = 'R'
    G = 'G'
    B = 'B'
    RGB = 'RGB'
    OPEN = 'OPEN'
    
    def initAlgorithm(self, config=None):
        # INPUT
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.R,
                self.tr('Red Band', 'Banda Vermelha (R)'),
                [QgsProcessing.TypeRaster]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.G,
                self.tr('Green Band', 'Banda Verde (G)'),
                [QgsProcessing.TypeRaster]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.B,
                self.tr('Blue Band', 'Banda Azul (B)'),
                [QgsProcessing.TypeRaster],
                
            )
        )
        
        # OUTPUT
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.RGB,
                self.tr('RGB Composite', 'Composição RGB'),
                fileFilter = '.tif'
            )
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OPEN,
                self.tr('Load RGB output', 'Carregar RGB de saída'),
                defaultValue= True
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):

        Band_R = self.parameterAsRasterLayer(
            parameters,
            self.R,
            context
        )
        if Band_R is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.R))
        
        Band_G = self.parameterAsRasterLayer(
            parameters,
            self.G,
            context
        )
        if Band_G is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.G))
        
        Band_B = self.parameterAsRasterLayer(
            parameters,
            self.B,
            context
        )
        if Band_B is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.B))
        
        RGB_Output = self.parameterAsFileOutput( 
            parameters,
            self.RGB,
            context
        )
        
        Carregar = self.parameterAsBool( 
            parameters,
            self.OPEN,
            context
        )
        
        # Abrir banda R 
        image = gdal.Open(Band_R.dataProvider().dataSourceUri())
        bandR = image.GetRasterBand(1).ReadAsArray()
        prj=image.GetProjection()
        geotransform = image.GetGeoTransform()
        # Abrir banda G
        image = gdal.Open(Band_G.dataProvider().dataSourceUri())
        bandG = image.GetRasterBand(1).ReadAsArray()
        # Abrir banda B
        image = gdal.Open(Band_B.dataProvider().dataSourceUri())
        bandB = image.GetRasterBand(1).ReadAsArray()
        # Criar objeto CRS
        CRS=osr.SpatialReference(wkt=prj)
        # Obter número de linhas e colunas
        n_col = image.RasterXSize
        n_lin = image.RasterYSize
        image=None # Fechar imagem

        # Pegar tipo de dado do array
        GDT = gdal_array.NumericTypeCodeToGDALTypeCode(bandB.dtype)

        # Criar imagem RGB
        RGB = gdal.GetDriverByName('GTiff').Create(RGB_Output, n_col, n_lin, 3, GDT)
        RGB.SetGeoTransform(geotransform)    # specify coords
        RGB.SetProjection(CRS.ExportToWkt()) # export coords to file
        RGB.GetRasterBand(1).WriteArray(bandR)   # write R band to the raster
        RGB.GetRasterBand(2).WriteArray(bandG)   # write G band to the raster
        RGB.GetRasterBand(3).WriteArray(bandB)   # write B band to the raster
        RGB.FlushCache()   # Escrever no disco
        RGB = None   # Salvar e fechar
        CRS = None
        
        feedback.pushInfo(self.tr('Operation completed successfully!', 'Operação finalizada com sucesso!'))
        feedback.pushInfo('Leandro França - Eng Cart')
        self.CAMINHO = RGB_Output
        self.CARREGAR = Carregar
        return {self.RGB: RGB_Output}
    
    # Carregamento de arquivo de saída
    CAMINHO = ''
    CARREGAR = True
    def postProcessAlgorithm(self, context, feedback):
        if self.CARREGAR:
            rlayer = QgsRasterLayer(self.CAMINHO, self.tr('RGB Composite', 'Composição RGB'))
            QgsProject.instance().addMapLayer(rlayer)
        return {}