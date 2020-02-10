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
        return self.tr('Traverse Adjustment')

    def group(self):
        return self.tr('LF Survey', 'LF Agrimensura')

    def groupId(self):
        return 'lf_survey'

    def shortHelpString(self):
        return self.tr("""This algorithm performs the traverse adjustments of a framed polygonal by least squares method, where  the distances, angles, and directions observations are adjusted simultaneously, providing the most probable values for the given data set.  Futhermore, the observations can be rigorously weighted based on their estimated errors and adjusted accordingly.""")

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
