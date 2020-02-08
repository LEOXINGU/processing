# -*- coding: utf-8 -*-

"""
LocalTangentPlane.py
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
__date__ = '2019-10-28'
__copyright__ = '(C) 2019, Leandro França'

from PyQt5.QtCore import *
from qgis.core import *
import processing
from numpy import sin, cos, sqrt, matrix, radians, arctan, pi, floor


class LocalTangentPlane(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    TABLE = 'TABLE'
    TYPE = 'TYPE'
    COORD1 = 'COORD1'
    COORD2 = 'COORD2'
    COORD3 = 'COORD3'
    GRS = 'GRS'
    LON_0 = 'LON_0'
    LAT_0 = 'LAT_0'
    H_0 = 'H_0'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return LocalTangentPlane()

    def name(self):
        return 'localtangentplane'

    def displayName(self):
        return self.tr('Local Geodetic System Transform')

    def group(self):
        return self.tr('LF Surveyor')

    def groupId(self):
        return 'lf_surveyor'

    def shortHelpString(self):
        return self.tr('''
This algorithm transforms coordinates between the following reference systems:
- geodetic <b>(longitude, latitude, h)</b>;
- geocentric or ECEF <b>(X, Y, Z)</b>; and
- topocentric in a local tangent plane <b>(E, N, U)</b>.
Default values for origin coordinates can be applied to Recife / Brazil'''
    )

    def initAlgorithm(self, config=None):
        # INPUT        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TABLE,
                self.tr('Table of coordinates'),
                [QgsProcessing.TypeVector]
            )
        )
        
        types = [ self.tr('lon, lat, h'),
                      self.tr('X, Y, Z'),
                      self.tr('E, N, U')
               ]
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.TYPE,
                self.tr('Input Coordinates type'),
				options = types,
                defaultValue= 0
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.COORD1,
                self.tr('Coord 1: Lon, X or E'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.Numeric
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.COORD2,
                self.tr('Coord 2: Lat, Y or N'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.Numeric
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.COORD3,
                self.tr('Coord 3: h, Z or U'),
                parentLayerParameterName=self.TABLE,
                type=QgsProcessingParameterField.Numeric
            )
        )
        
        GRStypes = [self.tr('sirgas2000'),
                          self.tr('wgs84'),
                          self.tr('grs80'),
                          self.tr('sad69'),
                          self.tr('corrego')
               ]
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.GRS,
                self.tr('Ellipsoid parameters'),
				options = GRStypes,
                defaultValue= 0
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LON_0,
                self.tr('Origin Longitude'),
                type =1, #Double = 1 and Integer = 0
                defaultValue = -34.94495050374325018
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LAT_0,
                self.tr('Origin Latitude'),
                type=1, #Double = 1 and Integer = 0
                defaultValue = -8.04943375547597206
            )
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.H_0,
                self.tr('Origin Elipsoid Height (h)'),
                type=1, #Double = 1 and Integer = 0
                defaultValue = 2.599625
            )
        )
        
        # OUTPUT
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )
    # Obter parâmetros do elipsóide
    def ellipsoid(self, model: str = 'wgs84'):
        """
        model : str
                name of ellipsoid
        """
        if model.lower() == 'wgs84':
            """https://en.wikipedia.org/wiki/World_Geodetic_System#WGS84"""
            a = 6378137.  # semi-major axis [m]
            f = 1 / 298.2572235630  # flattening
            b = a * (1 - f)  # semi-minor axis
        elif model.lower() == 'grs80':
            """https://en.wikipedia.org/wiki/GRS_80"""
            a = 6378137.  # semi-major axis [m]
            f = 1 / 298.257222100882711243  # flattening
            b = a * (1 - f)  # semi-minor axis
        elif model.lower() == 'sirgas2000':
            """R.PR – 1/2005 - IBGE"""
            a = 6378137.  # semi-major axis [m]
            f = 1/298.257222101  # flattening
            b = a * (1 - f)  # semi-minor axis
        elif model.lower() == 'sad69':
            """R.PR – 1/2005 - IBGE"""
            a = 6378160.  # semi-major axis [m]
            f = 1/298.25  # flattening
            b = a * (1 - f)  # semi-minor axis
        elif model.lower() == 'corrego':
            """R.PR – 1/2005 - IBGE"""
            a =  6378388.  # semi-major axis [m]
            f = 1/297.  # flattening
            b = a * (1 - f)  # semi-minor axis
        elif model.lower() == 'clrk66':  # Clarke 1866
            a = 6378206.4  # semi-major axis [m]
            b = 6356583.8  # semi-minor axis
            f = -(b / a - 1)
        else:
            raise NotImplementedError('{} model not implemented, let us know and we will add it (or make a pull request)'.format(model))
        return (a,f,b)

    # Conversão de coordenadas geodésicas para geocêntricas
    def geod2geoc(self, lon, lat, h, a, f):
        lon = radians(lon)
        lat = radians(lat)
        e2 = f*(2-f) # primeira excentricidade
        N = a/sqrt(1-(e2*sin(lat)**2))
        X = (N+h)*cos(lat)*cos(lon)
        Y = (N+h)*cos(lat)*sin(lon)
        Z = (N*(1-e2)+h)*sin(lat)
        return (X,Y,Z)

    # Conversão de coordenadas geocêntricas para geodésicas
    def geoc2geod(self, X, Y, Z, a, f):
        b = a*(1-f)
        e2 = f*(2-f) # primeira excentricidade
        e2_2 = e2/(1-e2) # segunda excentricidade
        tg_u = (a/b)*Z/sqrt(X**2 + Y**2)
        sen_u = tg_u/sqrt(1+tg_u**2)
        cos_u = 1/sqrt(1+tg_u**2)
        lon =arctan(Y/X)
        lat = arctan( (Z+ e2_2 * b * sen_u**3) / (sqrt(X**2 + Y**2) - e2 * a * cos_u**3))
        N = a/sqrt(1-(e2*sin(lat)**2))
        h = sqrt(X**2 + Y**2)/cos(lat) - N
        lon = lon/pi*180
        lat = lat/pi*180
        return (lon, lat, h)

    # Conversão de Coordenadas Geocêntrica para Topocêntricas
    def geoc2enu(self, X, Y, Z, lon0, lat0, Xo, Yo, Zo):
        lon = radians(lon0)
        lat = radians(lat0)
        
        M = matrix(
        [
        [  -sin(lon),                     cos(lon),                 0       ],
        [  -sin(lat)*cos(lon),   -sin(lat)*sin(lon),          cos(lat)],
        [   cos(lat)*cos(lon),    cos(lat)*sin(lon),          sin(lat)]
        ]
        )

        T = matrix(
        [[X - Xo], [Y-Yo], [Z-Zo]]
        )
        
        Fo = matrix([[15e4],[25e4],[0]]) # False E and N
        
        R = M*T + Fo
        return (R[0,0], R[1,0], R[2,0])


    # Conversão de Coordenadas Topocêntricas para Geocêntrica
    def enu2geoc(self, E, N, U, lon0, lat0, Xo, Yo, Zo):
        lon = radians(lon0)
        lat = radians(lat0)
        
        Fo = matrix([[15e4],[25e4],[0]]) # False E and N
        
        M = matrix(
        [
        [  -sin(lon),     -sin(lat)*cos(lon),          cos(lat)*cos(lon)],
        [  cos(lon),      -sin(lat)*sin(lon),          cos(lat)*sin(lon)],
        [   0        ,              cos(lat),                       sin(lat)     ]
        ]
        )

        T = matrix(
        [[E], [N], [U]]
        )
        
        R = M*(T-Fo) + [[Xo], [Yo], [Zo]]
        return (R[0,0], R[1,0], R[2,0])
    
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
        
        # Tabela de coordenadas
        table = self.parameterAsSource(
            parameters,
            self.TABLE,
            context
        )
        if table is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.TABLE))
        
        # Tipo de Coordenadas
        tipo = self.parameterAsEnum(
            parameters,
            self.TYPE,
            context
        )
        if tipo < 0 or tipo >2:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.TYPE))
        
        # Coordenadas
        coord1 = self.parameterAsFields(
            parameters,
            self.COORD1,
            context
        )            
        coord2 = self.parameterAsFields(
            parameters,
            self.COORD2,
            context
        )
        coord3 = self.parameterAsFields(
            parameters,
            self.COORD3,
            context
        )
        
        # Sistema Geodésico de Referência
        GRStype = self.parameterAsEnum(
            parameters,
            self.TYPE,
            context
        )
        if GRStype < 0 or GRStype >4:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.GRS))
        GRS_list = ['sirgas2000', 'wgs84', 'grs80', 'sad69', 'corrego']
        GRS = GRS_list[GRStype]
        
        # Coordenadas da Origem (lon, lat, h)
        lon0 = self.parameterAsDouble(
            parameters,
            self.LON_0,
            context
        )
        if lon0 < -180 or lon0 >180:
            raise QgsProcessingException('Invalid Longitude')
        
        lat0 = self.parameterAsDouble(
            parameters,
            self.LAT_0,
            context
        )
        if lat0 < -90 or lat0 >90:
            raise QgsProcessingException('Invalid Latitude')
        
        h0 = self.parameterAsDouble(
            parameters,
            self.H_0,
            context
        )
        if h0 < -1e3 or h0 >1e4:
            raise QgsProcessingException('Invalid Height')
        
        
        # OUTPUT
        # Camada de Saída
        GeomType = QgsWkbTypes.Point
        Fields = QgsFields()
        itens  = {
                     'lon' : QVariant.Double,
                     'lon_dms' : QVariant.String,
                     'lat':  QVariant.Double,
                     'lat_dms':  QVariant.String,
                     'h': QVariant.Double,
                     'X':  QVariant.Double,
                     'Y': QVariant.Double,
                     'Z': QVariant.Double,
                     'E': QVariant.Double,
                     'N': QVariant.Double,
                     'U': QVariant.Double
                     }
        for item in itens:
            Fields.append(QgsField(item, itens[item]))
        # CRS
        if GRS == 'sirgas2000':
            CRS = QgsCoordinateReferenceSystem(4674)
        elif GRS == 'wgs84' or GRS =='grs80':
            CRS = QgsCoordinateReferenceSystem(4326)
        elif GRS == 'sad69':
            CRS = QgsCoordinateReferenceSystem(5527)
        elif GRS == 'corrego':
            CRS = QgsCoordinateReferenceSystem(4225)
        else:
            raise QgsProcessingException('Unknown CRS')
        
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
            
        # Parâmetros
        a, f, b = self.ellipsoid(GRS)
        Xo, Yo, Zo = self.geod2geoc(lon0, lat0, h0, a, f)
        
        # Field index
        coord1_id = table.fields().indexFromName(coord1[0])
        coord2_id = table.fields().indexFromName(coord2[0])
        coord3_id = table.fields().indexFromName(coord3[0])
        
        # Gerar output
        feat = QgsFeature(Fields)
        total = 100.0 / table.featureCount() if table.featureCount() else 0
        for current, feature in enumerate(table.getFeatures()):
            att = feature.attributes()
            coord1 = att[coord1_id]
            coord2 = att[coord2_id]
            coord3 = att[coord3_id]
            if tipo == 0: #(lon,lat,h)
                lon, lat, h = coord1, coord2, coord3
                X, Y, Z = self.geod2geoc(lon, lat, h, a, f)
                E, N, U = self.geoc2enu(X, Y, Z, lon0, lat0, Xo, Yo, Zo)
            elif tipo == 1: #(X,Y,Z)
                X, Y, Z = coord1, coord2, coord3
                lon, lat, h = self.geoc2geod(X, Y, Z, a, f)
                E, N, U = self.geoc2enu(X, Y, Z, lon0, lat0, Xo, Yo, Zo)
            elif tipo == 2: #(E,N,U)
                E, N, U = coord1, coord2, coord3
                X, Y, Z = self.enu2geoc(E, N, U, lon0, lat0, Xo, Yo, Zo)
                lon, lat, h = self.geoc2geod(X, Y, Z, a, f)
            
            #feedback.pushInfo('lon:{:.3f}, lat:{:.3f}, h:{:.3f}, \nX:{:.3f}, Y:{:.3f}, Z:{:.3f}, \nE:{:.3f}, N:{:.3f}, U:{:.3f}'.format(lon, lat, h, X, Y, Z, E, N, U))
            
            itens  = {
                         'lon' : float(lon),
                         'lon_dms' : self.dd2dms(float(lon),2),
                         'lat':  float(lat),
                         'lat_dms':  self.dd2dms(float(lat),2),
                         'h': float(h),
                         'X':  float(X),
                         'Y': float(Y),
                         'Z': float(Z),
                         'E': float(E),
                         'N': float(N),
                         'U': float(U)
                         }
                         
            for item in itens:
                feat[item] = itens[item]
            geom = QgsGeometry.fromPointXY(QgsPointXY(lon, lat))
            feat.setGeometry(geom)
            sink.addFeature(feat, QgsFeatureSink.FastInsert)
            if feedback.isCanceled():
                break
            feedback.setProgress(int(current * total))
        
        feedback.pushInfo(self.tr('Operation completed successfully!'))
        feedback.pushInfo('Leandro França - Eng Cart')
        return {self.OUTPUT: dest_id}
