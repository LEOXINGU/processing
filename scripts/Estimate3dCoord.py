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
    OPEN = 'OPEN'
    
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
        txt_en = 'This tool calculates the coordinates (X, Y, Z) of a point from azimuth and zenith angle measurements observed from two or more stations with known coordinates using the Minimum Distances Method.'
        txt_pt = 'Esta ferramenta calcula as coordenadas (X,Y,Z) de um ponto a partir de medições de azimute e ângulo zenital observados de duas ou mais estações de coordenadas conhecidas utilizando o Método das Distâncias Mínimas.'
        dic_BW = {'face': 'iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMMwAADDMBUlqVhwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAIUSURBVEiJvZa9quJAGIbfMfEYTUSUQAqLYOnehJobsBTlHLbRQtKKlY3lObegxRa7pRdg7y0saiuoKAErMZif2Squ2eTEOCfsC1Pk+3uYb2YyQwCg1+u9UUqHAKoAOCQrB8ASwPt0Ov1JdF3/bprmj4QhoXp5eXnjTdMcUEr/Bw+WZQ15Smn1q4UIIZBlGaIoghBys2+3W1yv19u367rfeAAc6ww5jkOz2USj0YAoigH/aDTCbrfzpfCUUrAC2+02NE2LjPm3NjNQkiTU6/WHsFAgi1RVRSqVCthd171BwmozA/P5fMA2n88xm81g2zYAwHGccCAL9H43elosFrhcLpE5zMCwHMdxImtRSp8DptNpZDIZAIAgCAG/IAi+42Ga5q29nkin06FxgZqmodvtxooFgPF4jPV67bM9NcNnW384HJI7h49kWRZOp9PXgOfzGfv9HgCQy+VQKBR8fsMwYFkWAOB4PMJ13UAN0mq1Yq/hfVytVoOu6z7/YDDAZrP5Wzzk6CR6LOLEJLqGcWrxYX2OW5wJmOQOjQX0ApOERgIrlQoTUJblgK1cLodeWZ4IIeDDngZx5P1T75XNZiFJUmQeTyl1wPAW/awrD7rlpDiOW3qL/cz4DBY1CCG/U4qifDw7O1YpivJBAGAymbwahjG0bbtKKeXjJJdKJaiq6rOtVqvAjU8IsTmOWxaLxfd+v//rD1H2cZ8dKhk8AAAAAElFTkSuQmCC', 'github': 'iVBORw0KGgoAAAANSUhEUgAAAB0AAAAdCAYAAABWk2cPAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMOwAADDsBdtCd4gAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAW2SURBVEiJrVZdaBNZGD33TpL+RosxxWZSu7ZpDYQ1CPVBUSws2Cq6sPWvFW1BQcyKaOnDwvqgQvFh6ypoFn3xUd1OygrarK6UKoq7FAqFVWulKba1rtVgW5PWZjqZ++2DTjY/av3ZA8Mw3537ne+c+829w/ARIKKFQ0NDG/v7+zeEQqGysbGxopmZGVteXt5Lh8PxrLy8fNDtdgdlWe5gjL2cKx/70GAkEqkIBoMtiqLU9vX1SVNTUxBCQJIko5g3SRiD1WqF1+vV6+rqfqupqTmcnZ098EmkRGS5cuXKTydOnPh+cHDQzDlPHgPnPEGYSMQYhBBgjMHtdmuHDx/+paqq6gfG2OycpJFIxHbkyJH2QCBQ9SEX5gLnHHv27Pmzubm5Nj8//3nymCn5YWxsrLCxsfGv7u7uUkmSMtR8CoQQOHfu3KqRkZG70Wh0pdVqDWeQEpF569atSnd3d6lhn67rifX7GBhFCiHAOYfJZMK1a9fKOOeXiegbxpgKAImMmqad7Ojo2A68WZ/169fj4MGDyM3NxdDQEDRNA2MMRAQhRILEWEcAsFqt2LZtG/bt24eJiQmMjo6CMYZHjx4tNplMedevX/8DeLumd+7cqdixY8d9IjIzxqBpGi5cuIC1a9cCAEZGRuD3+6GqKjweDwoLC2E2m6GqKl68eIF79+7Bbrdj//79sNvtYIxBURQ0NzeDMQbGGLKysrT29nbP8uXLB0wA0Nra2kJEZqN6zjkWLFgAo2uXLFmC1tbWhCLjnm6t0cEAYLfbEzEAiMVi5jNnzrQA2M47Ozttvb293xmTjZfGx8cTVQJvujH5OR3J73HOMT4+nhJnjOHmzZube3p6FvJgMPitECK5oZCVlYX8/Pz3d8wcEEIgNzcXFoslpShVVaXOzs4NksVi+XFyctKTTFpfX4+Ghob3qpoLRASXy4W+vj6EQqEUtZqmxfmTJ09cyRMkSUJ9ff1nkRkwLN65c2fiMzLug4ODX3MhRFHyJjBv3jyUlJR80cYAvFFVWlqKnJyclHgsFnOYdF1fkGyjyWSCJEmfbS3wnyqLxZJoQANCiDwOIOUoisVieP369f+iNBKJQNO09FzTnHP+LDkyNTWF4eHhLyYUQiAUCkHTtJQxk8n0D8/Ozh5MnxQMBqHr+hcTX716NcVaxhjmz5//N3e5XL+nW6koCoaHhz/bYiJCb28vbty4kRIXQmDp0qUdfPXq1VeJKG5s5gAwPT2NvXv34vHjxymJPhYPHz6Ez+eDqqrpxejV1dW/MwAoKytTVFXd6vV6sWbNGly+fBmjo6Ow2WzYtWsXamtrUVxcnOjE9D8JXdcTa9je3o6LFy9ienoayUIAoKCgQLl///52AIDP5yuVZVldtmwZBYNBGhgYoI0bN5IsyyTLMpWUlNCqVauoq6uL4vE4paOtrY0qKytp8eLF5HQ6SZZlcjqdKZfD4Zg9evSoC0j6XfF4PKdevXp1yGKx4NKlS4jH4/D5fAiHw+Cco7CwELdu3YLVak1pDiJCOBxGVVUVotFoip3JShctWnSyp6enGUg6xFtaWrpu3769Rtf1r54+fYrdu3dj5cqVKCoqgsfjQWNjI9xud8ZJwxiD2WxGMBhEOBzGuyBJ0t1jx441BAKBzE/i+PHjdofDEXI6nXTq1CmKRqM0MzNDExMTFIlESNd10nU9w97Z2VmqqanJsPSt1aHTp0/bUxx4B7Ht7Nmz7URUVV5ejhUrViAnJwcFBQU4cOBAxrYGAJqmYdOmTXjw4EGKA5zzu01NTZsPHTr0PJ0nA4qiWLxe70mHwzEryzI5HA6qq6sjTdMyVBpKq6urqbi42FA3W1lZ+bOiKJY5ydLR1NTkqqioaCsqKopv2bLlg6Tr1q0jWZY1j8fzq9GlXwS/328LBAIN8Xi8Tdf1fiKafMs3KYTo13W97fz58w1+v9/2Mfn+BQw/D7WnyIOMAAAAAElFTkSuQmCC', 'instagram': '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', 'lattes': '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', 'linkedin': 'iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAYAAACpSkzOAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAM6QAADOkBmiiHWwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJRSURBVEiJ7ZU/aCJREMa/t7soa5LOoGihktZOQSxSWykBIYVaWZ6NVa6wSZ/WI5BGziJypA1CQBLsgkKKgBjFQkEtkouJ+AdxdeeKnHvurXdcXK84uK/amfl4v9m3s++xbrdrury8PGm324dEZMYGxRj7arPZvoRCoSPh/Pz8pFqtftgkYEnmTqeT6PV6xDscjs9EZPpLIADAy8uLS5jP52bGGACA4ziEw2H4/X5IkoSrqytcX1/rBhHRrrCcCAaDCAQCShyJRPD6+oq7uzvdMG458Hg8GoPX69UN0YDG47HGsCqnG5TP50FESjyZTFAoFDYCYvF4nBbDAAB7e3vw+XyQJAnFYhGPj4+6IUQE4eekJEm4vb0F8DaFC1mtVphMb3+BLMtotVogItjtdjgcDhiNRvT7fTw8PKzcbhXI5XIhlUqpOkkkEpjP5zg+PoYg/LCfnp5if38fbrdbteB0OsXFxQVubm5+DTIYDKoiYww8z4OIwPO8qhaLxbCzs6Pp3GAwIBqN4vn5Gff390qe0zj/UKsgywqFQqpY843eo1KphHK5DLPZjIODAxiNRqXmdDqxvb2N4XCoD1Sv13F2dqbEs9kM0WhU5bFYLApo7a1bTOZClUpF49na2lKe1wb1ej1VvGqklwdobdB79R/0j4FkWdYYiEh1dawrAcATgF0AaDabyOVyyuE5HA4xmUwAAJlMRjl2ZFlGo9FQLTQajZDNZiGKouKp1WqL8hNLJpPpwWCQ0N3ybySKYpqLxWJHjLFP399s03riOC4dCAQ+fgMeouMzfwx22gAAAABJRU5ErkJggg==', 'RG': 'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAcCAYAAAB2+A+pAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMfwAADH8BdgxfmQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAM2SURBVEiJtZdLSytJFMd/1dXB+OiQRJEQBEnbPgISJGIQcePKjyBZzoP5AH6OuR9gFjPMznwC1650EbKSy00WPhJ8EMlDtG1M0p2axZCA1871cZM/NDRFnfqdqjrnVJUAODg4+E0IsQ8sA5LRyANKQogve3t7/4hcLvcH8NeIYL5SSv2uAftDHhSl1A/7CCH2dWBxWNBoNIppmgSDQarVKufn53ie59d1RQO0YUBjsRg7OztomkatVmNpaYnNzU2EEH7dNX0YUKUUpmlyd3dHPp9HKcXV1RXT09MIIXyXfihgKSWGYVCpVPoQ27axbXugjS/4HcHh29btdlFKsbq6SiwWA6BQKHB/f/82WEpJKpUiEAi8aA8EAiilaLVaNBoNrq+vabfbr+BCCG5vb3l8fCSTyaDr/ov6KrA8z6NcLtNqtUgkEszPz+M4Ds1mE9u2MQyDjY0Ndnd3mZmZ6ds4jkMoFAKg0Wjw8PCAEIJOp+ML9nWnZ5hIJJBSUiqV+gMIIbAsi3Q6zdbWFoeHh7iuS7lcZn19HcdxsG0by7Ko1+sD93lgcCml6Ha7SClftZ+dnbG4uIhhGMzOznJzc0OlUkHTNBYWFtB1nXq9zunp6aA8/lxUe57H09MThmEwPj7ed+ji4oLLy0uEEHieNyiHPw+WUjI5OYlS6lXE9krmj6DwyaplmiaGYVCtVqnX658Z4u0ZCyGIx+O0223GxsaYm5sjHo9Tq9U4OTn5FPRdYCkly8vLCCEIh8MopSgUCpTLZVzXHR3YdV2Ojo7wPI/t7W1isRjBYPCnoPDOPVZK4XlePz2SySThcHj04J4ajQbFYhEpJZlM5lWOjwwMUCwWaTabRCIR0un08MG9gt/778l1XfL5PJ1OB9M0WVlZGR54amoKy7IIBoPouo5lWYRCof7SNptN8vk83W6XVCrF2toaExMTHwKLXC734vCVUpJOp9F1/cW5rGkapVLpRcGIRqMkk0kikQiO43B8fMzz8/O7wd73Mx90EfArg0opNE178/LwnboaUPID+H2DnPkgFOCbppT68lGrn5VS6k8tm83+DfwKfOX/Z8ao5AFflVK/ZLPZf/8DudZq3wvXLmgAAAAASUVORK5CYII=', 'tweeter': 'iVBORw0KGgoAAAANSUhEUgAAABoAAAAaCAYAAACpSkzOAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMMQAADDEBLaRWDgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAK5SURBVEiJpZU7T+NAFEZP4kAePBwZ8TA0EUIRKKIgQhSImnZ/wDYr7Q/barddbRu2QVAQhChAgBQqQClwFEIcx8IYfLdKNk5sJ4GRRh6PPN+Z+90749jZ2VnGsqyfwD6QEREARISocdRcT7dF5AD4lmi327+AL0GCn4QgIhkR+SIiPxIish8k3i/yQVCn7ydEJD0sgjDBMUCZxCg2hQmqqsri4iKKotBoNKhWq741vesSvULpdJrJyUkajcZQy7a2tlheXqa3FQoFzs/PmZubQ9M0Dg8Pu2vivQJLS0sUi0Wy2WykFfl8fgACkEql2N3dJZfLcXFxgaqq/0G9O04mk8RiMba3t8nlcqHRrK6uDkB628TEBDs7O5imORgRgGVZ3Y/z+Tx7e3ssLCz4QMlkkng8HglqNpscHBzw9vbmz1EHVK1WWVtb6wpNTU1RLBZ5f3/HMAzq9TqO40RCAGq1Gq7r+jboK4aZmRmurq7Y3Nz0LVQUBV3X0XV9KATAcZwBy7vlLSJomjbU/1Ha8/PzAMhXdQ8PD5+GABiGEQ1qt9tcXl5+CvL09MTLy8ugdf0T9/f32LbNxsYGs7OzY4Our68DD/oASEQoFApMT0+PDTFNk7u7u0BQPAhULpdxXXds0PHxMZ7nDUBCQa1Wi1KpRKVSwTTNkSAnJyfU6/XQWz4QJCI4jsPj4yOKogyFnJ6ecnt7G3nTd3OUSCSYn59HURRUVUXXdTKZTCTAtm2Ojo585dwP6rx3Qa+vrzSbTdbX11lZWSEWi4UCLMvi5uaGSqWC53mh/67esa/qTNOkXC4DoGka2WyWVCoFgOu6tFotDMPAtu3QXISNA8tbRKjVaoEnPCwPYZZ1nnHP8+ww2Ed7P0RE7LjneX/7ff6ocES0pbiIfBWRP57n2aMAwywKGdsi8ltRlO//AFPkniYXwGRMAAAAAElFTkSuQmCC', 'udemy': 'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAdCAYAAAC9pNwMAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMOgAADDoBpJd/BgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAYHSURBVEiJlZdbTFNbGsd/e/cCFtpgxX0sjHgJoepBJcqMl4gGjoYTb5PRYZxEMmq8cI5Oosw8ODG+iJpMHGN0Hsz4QHwwmRgLHpJjqkDqQZ+QWEWisdEIRZoKtAKFFuxt73nQ3aG05pT/2/rW5fd93/rW2msL/Lo0gO727dtlc+fO/cFoNK41mUzzjEajMR6Py6Ojo4FgMPjR4/E8fv369fULFy70A1EgnsHaaSVarVbj3bt3L/b3948pGSgWiylPnz71nj9//kcgBxBnC9Vfv379QG9vb0bAmZJlWXn06NFATU1NFaDPFDrn5s2b/56ampIVRVGCwaDS2NioNDQ0KG1tbbNy4MOHD7H6+vp/AHNmQjQzoXfu3Gnav39/rVarFQCam5vp6ekhHA7jdrtZs2YNBoMhowhyc3PFLVu2fOf3++c6nc5fgFg6sP7atWv/OnjwYK0gCAD4/X5aWlqQZRkARVEoLS3FbDZnmj20Wq2wcePG375582bM5XI5+VJ06uaLdXV1fzh27NhfRfH/9dDe3k40Gk20BUFAp9N9FdLd3c2VK1e4desWk5OTCbvZbBYaGhr+aTQaf6cyVYqhpqbmWnZ2tqAO7u3t5fnz5zO9Z968eWmhIyMj2Gw2vF4vL168wOFwJPWvXLlSe/z48f8ABhWsPXXq1Mmqqqpv1EHhcBibzZZIsSpJksjNzU0LfvjwIeFwONF2uVwoipI05uTJkyskSfo9oBUB/fr16+vUfVUUhaamJnw+X8riJSUlaaHDw8M4nc4kWzAYTNomAIvFIuzYsePvgF7MysqyVFRUFKqdbW1tdHd3pwVYrda09pm1ACDLckrGAKqqqr4FFmh37979l4KCAlFRFFpbW3E4HCkpAtDr9SxatCjF7vF46OnpSbGnWwOgsrJSB3ynlSTp28nJycR5/dqEoqKitBXd2tpKPJ56LSuKkjZii8UiZGVlWUWz2fwbv9+fBJ1+pFQtXbo0xfbu3TtcLhcA8+fPT5ony3LaIERRZMmSJUtEILeoqIjt27djtVrZtm0bmzdvTpmwePHilIju3buHoigIgsCmTZuS+mOxGJFIJGUOQFZWlln0+/1+gMrKSo4ePUp1dXVKRQuCQEFBQZKts7OTgYEBABYuXMiKFStQT4YKmX6JuN1uLl26xPj4OH19fV7t8PDwwMzoPB5PUttoNJKTk5Noj42Ncf/+/YRTW7duJScnB51Ol7Tfb9++JT8/n66uLux2O9FolIGBAWV8fNyjffz4cWcoFKpVFw6FQoRCoSSwwWBg+jlvbm5ORFNcXMzy5csRBAFJknj//n1int1ux+FwMDU1BYDJZKKvr08B3oo+n8/e3t6eOISRSCSlGqcXSUdHR6KgNBoNO3fuTDhVXl6eNE+W5QRUEASqq6ux2+2fAIcIDLW3t7vUwRqNJmmvAD5+/Mjg4CBOp5MHDx4kHKmoqKCwMHH3sG7dOpYtW8ZMZWdns2fPHsrKyrDb7Z3AkABo9Xr93q6urv+uXr1alGWZc+fOpaR7eqrhc0GdOHECrVabkp1Xr17hdruRZZkFCxZQWlqKwWDg6tWr0fr6+v3ATxpAjsfj/YFA4Pu9e/cWCILA0NAQXq83xXNVeXl5HDlyJKngpjsoSRIlJSVYrVYKCwvR6XSMjo5SW1vbMTExcQH4pD4EYi9fvnxZWFj457Vr1+osFgvPnj1LuX/h8xfq8OHD5Ofnf9WxmZJlmQMHDow9efLkCOAGFBWs8Hmv+8vLy3etWrVKLC4uxuv1MjExgSAImEwmNmzYwL59+8jLy8sYCnD27NlPN27cqAMcTHv+TNcci8VypqWlJaK+FgOBgDIyMqJEo9FZvzZjsZhy5syZSeBvpHnwpcA1Gs2fLl68OBaJRGYNU+Xz+eRdu3YNA3/MBKpKD5SVlpb+3NjYGI7FYhkDg8Ggcvny5U+SJDUDZcziXa1K5PPfQGVZWdnPp0+fnujo6IgHAoEU2ODgoGyz2WKHDh0as1gsTcAWfuVPQvhaxzRpAB1gBNZ9iUISRfGbLzfcIDAMvACeABNk8O/0PwJCxMb99V7LAAAAAElFTkSuQmCC', 'youtube': 'iVBORw0KGgoAAAANSUhEUgAAACEAAAAaCAYAAAA5WTUBAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMNwAADDcBracSlQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAKkSURBVEiJxZcxSBthFIC/918uGhxMsyptcGjoIgGHW9wSihQKGZrNthHsIC7S1TqWgkRwcZV2lKo0FouixaEuEQ4khIIdrClkEoIZgiae93fQgFgll5jqt93x3v++e3f/3TvhGgYHBx/UarUUEAMeA48A/3WxDagBf4A9EdmsVqsfd3d3j64GyeWDZDJpFAqFKWAC6G6haCPKIjKTzWbfA+4/Ev39/V2dnZ3LwNP/UPwqaycnJy9yuVwFQF2cVIFA4PMdCQAMBQKBL8lk0gAwACzLmtJav7kjgTp95XK5ViwWf0g0Gg36/f7fQLBRltYaEWkU5hkRKTmO06dM03ztRaAuEQ6H0Vq3RUJrHTIM46XR29v7jvNt2BClFEtLS0QiEfb39ymVSrfujIg4Cog0mxiPx1lYWGBycpKenh5c122cdANa64gCHra6QCKRYHl5mfHxcYLBII7jtLJMWAEdrUrUSaVSrK6uMjo6SigU4uzsrJn0DtU4xhs+n4+xsTFWVlYYHh6mq6vL821qm0Qd0zSZmJggk8kQi8XuR6LO1tYW+XzeUzd87S6ey+WYnZ0ln88jIijV+DrbJnF4eMj09DTb29u4rtvU+8MHVLnFDjk+PiadTrO+vs7p6WkrS1R9QAGPb8zLaK2Zm5tjcXGRSqXiqe03sO8D9pqVyGQyzM/PUywWMQzjNgIAv3xa600Ree4l2nEcRkZGODg4QCmFYRi3KQ6AiGzIwMBAt2EYB9znp9y27bLWesZjUtsELkjbtl2ur6osy/qqtX7W7io3ISIb2Wx2CHDrT5TrOE4SWLsjgW+O4yS4mLiv9ldZljWptX6Lx2mrSY6A9M7OzgeuG/kvE41Gg6ZpvhKROPCE85mj5Z8fEfnpuu5313U/2bZdvhr0F9Fo9phaoDu9AAAAAElFTkSuQmCC'}
        footer = '''<div align="right">
                      <p align="right"><b>'''+self.tr('Author: Leandro Franca', 'Autor: Leandro França')+'''</b></p>
                      <div align="right">
                      <a target="_blank" rel="noopener noreferrer" href="https://www.udemy.com/user/leandro-luiz-silva-de-franca/"><img title="Udemy" src="data:image/png;base64,'''+dic_BW['udemy']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/GEOCAPT/"><img title="Facebook" src="data:image/png;base64,'''+dic_BW['face']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.youtube.com/channel/UCLrewDGciytcBG9r0OxTW2w"><img title="Youtube" src="data:image/png;base64,'''+dic_BW['youtube']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.researchgate.net/profile/Leandro_Franca2"><img title="ResearchGate" src="data:image/png;base64,'''+dic_BW['RG']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://github.com/LEOXINGU"><img title="GitHub" src="data:image/png;base64,'''+dic_BW['github']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="https://www.linkedin.com/in/leandro-fran%C3%A7a-93093714b/"><img title="Linkedin" src="data:image/png;base64,'''+dic_BW['linkedin']+'''"></a> <a target="_blank" rel="noopener noreferrer" href="http://lattes.cnpq.br/8559852745183879"><img title="Lattes" src="data:image/png;base64,'''+dic_BW['lattes']+'''"></a>
                      </div>
                    </div>'''
        
        if self.LOC == 'pt':
            return txt_en + footer
        else:
            return self.tr(txt_en) + footer
            
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
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OPEN,
                self.tr('Open output file after executing the algorithm', 'Abrir arquivo de saída com coordenadas 3D'),
                defaultValue= True
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
        if output[-3:] != 'xls':
            output += '.xls'
        
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
            A[3*k:3*k+3, 3+k] = -1*self.CosDir(Az[k], Z[k])
        
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
        s_x = round(float(sqrt(SigmaX[0, 0])),3)
        s_y = round(float(sqrt(SigmaX[1, 1])),3)
        s_z = round(float(sqrt(SigmaX[2, 2])),3)
        
        # Slant Range
        slant_range = []
        s_t = []
        for k in range(len(Coords)):
            slant_range += [round(float(X[k+3, 0]),3)]
            s_t += [round(float(sqrt(SigmaX[k+3, k+3])),3)]
        
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
        
        
        dic_color = {'face': 'iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMMwAADDMBUlqVhwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJxSURBVEiJvZY9TBRREIC/t/vujuMOROBilEQTDOLRWFoYhRgrIjY2FCAWmkgwVkKljR30mhALf4KxMSR2GmtbYzSG+JMYNYgokUDk4LjdHYuD4/Z272f30NnsJjvzZr6ZN2/fWwXQf+XhsDgyIZAGTHZXbAVzoph8Nj0yo85fmxlZW7fu7zLEV6JaDevMhnVd5H/gYMOSCe04kq6XZyDsa0/SnIih1I7+8/wK2Zy9oxB6tIAZtkJtwPC5Y5ztS9OUbPDYL9+c5cvCauFdgalFBEIABRgdPM7A6Z4qA3eCC6BFhDAVNiei9PcercISnKLgKg8kVIVdh9owTcOjt22nACmNXagwDHBPk7dnT56/5d7sKyzLAcByHE/s0FNqFC/HLXnx8iOZjVxZH1UPUHycLNvx1Rd82OphrcBoxCAeze988Zj22JMNmubGSOE9k7XIWe7g6tTQdKWkXDLQ1834pd7aBgNXbz3lzYdFly7QlErA1TW/uOKZ4mA9DMDLblosLa8huBdXIOCfTJav35cBSDRGaWtJuOw/fq2yubV3LvxcxXGEEh7qxODtmnsoRc/+k93cGDvjsl8Yf8ynb7+3Q5eygHo+i3LzK5VHhAb6OeVjVQ5WR4V+OfxDoK9TFaACNCE370CJbJsA3dl5IFSFqVSLR9fRkcI2Y+WdFOhEwnvM1CLRWMSji8djJH1+NYpFA7ZIiH9RvxZSZT0obCNiOnNsn8xB7nJJVLhN5J1xpH1zSnDy2QW6yjHLX4dT61MK4M7dB0MLS9mJnGWnEfEedD6Sam2k62CrS/f6/SKZ9ZITXylLm+bc/r3RybHRi4/+And1Z9yayEQKAAAAAElFTkSuQmCC', 'github': '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', 'instagram': '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', 'lattes': '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', 'linkedin': 'iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAYAAADE6YVjAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMagAADGoBEqIqpQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAJaSURBVEiJ7ZVfSFNRHMc/53rbrDk3XcMK1zZQygiTQM3SIggKInzopV4iiCjIUAjxseihhwyjiPApDUKCerAICjIqFbQ3o6ykObYKtGy7W9mazO320Jz3OpLhNeih79P5fX/nnM8993f+iPFw2Nb6IHDVNzXdiIqNhRKAukj8JwminuKC3suNnmZRf3345mBQOZLDsCWpaq21W8htj5RZVLs2UWiWiSWSzKZy+eTFJRAROaUBlNryuX14C3XuIqamZzh9/y13Xk0agqiqape0xo2Dm9nhKUISUGI1c+tQJW77SkMQAEnbaPAW6ZKmPIlaV/ZeWDIkBYxNxbI6jH39sXwQgKZ7o4RjCQBUFS4+8/Ny4rthiJDaHqopjWHPl6kutfEhEl+WVaCCrI3LHKs4s9OLJH7Hz/1hekYm2Oi00FLvQaT9Ab/C3deTHK9xsbd8Nc4CE9/iswwGFK4NBQml/8acdJDd3mJO1roy8QaHhZ6RCXZ5izmh8atKrJyqW882t+54safcwbHqUho6hwlG4hlfV5NcVeO2ZwHm5LLnc+XAJp23JMicxkMx3n3Jrtv+CidOi8k45Hyfj7L2fio6BmjqfaPLyZJg67pCYxAlluDCU38m7nzxEWVBsddYzcYgo5+nmUnOb/ykqvIpGtf1KTDlGYMkkqksL7nwxhbzTUOFz1X/If8eRAYRIf0EP/aFaO8PZC7CoYACQJ8vxKWBQGbQcFDJmqhjMECl5gA+eR9Kt0REOM71dYV+Jo7+lSUAlhV5XdLZfe5mSdANRJd3ehGRULtat3tbfgEYZ8EeNElUHQAAAABJRU5ErkJggg==', 'RG': 'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAcCAYAAAB2+A+pAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMfwAADH8BdgxfmQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAOqSURBVEiJvZdLaFxlFMd/57vzajIzTpIxJhNLam0akyyKuqgiFVpdlBTXUiqEaipIBInixpUirjRClS5qsfjAhQvRjQvBtgvFZKE1i+apLU1DXm0ydWYyr/v6XMxNJelcm8SJB77Nved8v/Od87/n4woA4z++BPI60AkY7Iw5wBRahug5cl6YuPgyWp/dIZiP6X5h/MIklZPWaE8NaBABxM9rPAB01IInwBPhKP2JVpoCIS7lb3M+s0BO62rujyhA1QJ8tC7BD+2PERDFcDHLq427+SLVQ7C6uwrUAipa059I8VPhNqcWJzGB73K3OBiJIyJe+ddbTcARgX2hOr7JLmF6fZ2ySkxZJd+Y6mDt+rgLFeGs745CCIiipF3QmneTezhS3wjAwNI0o+X8vcH1IrzX3EHDhi7ElYFGc8ux+bWY4dvVZZbdSoIajcYlgIDA9/k0U2aRs6kuYqr6WLhLWEWt+TqzyLJj8UJDiufva2HBKjFayvKnWWRvqI4zqR5+f+ggT0fiXgzMWiZd4SiGhpFSjslyDoWQc2yf2o1fqKr3RlFM7HuSiCj2/vEzK175A8BAoo2hlk4W7DIHro6Q1i59sWZOt3ZyZmWGa2aJU40PYmnN0dlR8lXE5fsp2biUPZiwNgwEG+HcX/NcNQu0BSMcqksA8FXuJm8uTnM4mmQw2c5EOc/xuStVoWsH2LIVtMuMVWZ/uJ42I+QlCueyS3yeXSJApWVafCfX9sB1otgTjGBrzai5uu6d6S3+BQrbmFoGmv5EKw+Hd3Epn2aklNvqFsAmThwQoTfaRNq1ecAI8VzsfnpjSYYLGU7MjeH6XwT/DRwWg8GmdgygOxLDRjO4MMmX2SWyPsLZjN2z1HnX5tjMZQ5d/42L+RVComgJhMn5TrcagaEilgyad25eo+A6vJZs5/FQ/c6D12y4nOPj5etEVYBPUt3E/i+wi/B++gaXixke3RXndEsnBtvrsy/YQAgi3s3zj3LTWvPKwgRpx6IvkeKtht3bghsM9L29MZP9wTAn4y30xpsJKUXBsUk7JjnXxUIz75jMmgWOxZo5HG2iURTTZp6s62w6hbsuiZgIHzV3UK8MLG8bhRAU4cP0DX4prXqB8FQ4yhvJdg5E4sxbJY7PXWHWsTYNdthQcrnzfeo7bkDV2StaEwZsNLZsWjKuAqY2PtUi3lLeEt+Br0UoiWwFCjChQA9tJaImJnyg6H72UzQvAmNUfjN2yhxgDOEkXc989jdK2myw4HcGQgAAAABJRU5ErkJggg==', 'tweeter': 'iVBORw0KGgoAAAANSUhEUgAAABwAAAAcCAYAAAByDd+UAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAANIgAADSIBbrwGKgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAONSURBVEiJpZbNixxFGIefqumeGfd7R9xoks2usAaChkg8iJ4SwYMIgSCiZ0E9iBD/Ar1H9CA5mZsfIKjJWQ+eVklMCHETgwkYDetmWTMzOzM7PTM93f3m0NvT1dM9H64Fw1RX9VtP/3719tulPvpJinqaz0TkNWBeRAAw/8OuZPSzrjPGkGrgy7eBX3nf0lOcE5G3+iEIyG5QDE72B8HC+xLj8yBvq9yctgQ5PTbMGM+6HgKM5k5bCPOCGRw/dXLBcazcHQ9tzJorWUnYoH3rtzKe1wgHZjTFnKLs+Gw1/QGwMMYyF9MKZvNQbg23MoI9u2BxaqXApK2I2t81j69u7FBrC8f2FUCEX9ZbvTj14SVPokUPzyteXdacv9FluzM8MY7vs3jzSJGs5vpCTisqLZ+zq1XaXoAfBIiANhXsn4S5guLdozYHp9SuugxbtHBqpZAJA8jnFIEId6td3nhmCkvTSyYthl1eEAZM5xXvHM3z8pKNrdN7sTyTY8KwMavZWrE8Z3PhVoN21+/FWqZdf277cCgHgFZwctHi+cdzXN70uLbZ5X4zDJywhrJ67ePVMjuu33NGRMKkiWy91wi4VfE5Usr1giZsxYlFmxOLNs2usNHwkTFgIuB0gwRM6AEBhOMLOf6qBeyf1MwW0pZN2oqnSuPJc3qJkgEMnyhU+sqT+bEWHNXu173M6qN7dBHW/vVouOMYNrr9Ue6k1IkI2kyathfwxc0WHf//Q6+sO4nMjl4v3Z/yd7d9zl1tcn2rS7BH7u1yh3/qbkpdIktN+S8tFTm2YO9Z3cXfa/F6mMWDtEJEuHjbodoO9gT7+V6TOw/acaKYYsiwVBDqnYBPL9X5daOD+x/2c73W5evr1cRaiSxN7mHy81Pv+Hy51uDza3V23NFqNxpdPlnd2i1j/eriD7LVDwRhylaslGxeOFDk8KOj9/K3zRbnr5RxjDJmnoHifSQGPmIpTi4VefFgcWRhjtoDx+PCzRqX15vJxDMAZh8E9cGPFTEVTucVzz2R5+nH8hyatSlaMVwEyo7HnbLL1Q2Htc0WfmCeX/rPM5HSGKzO/FCW7JvDX9FS2Br8QHBcHy+QAWrSVvbDDEvNY2AS6LjBgIdJqxlmZfSvRaSaejUyioGQMZeR9sNgIlQ0It8PByZrYbaVSfUDYCjUd5ZI7T2RGQ+R1wUpkYKl92mYlf2QSBmKb1zbO/MQw3IUMFMV01gAAAAASUVORK5CYII=', 'udemy': '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', 'youtube': 'iVBORw0KGgoAAAANSUhEUgAAACIAAAAbCAYAAAAZMl2nAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAMZwAADGcBG5JHNgAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAItSURBVEiJxZe/a1NRGIafNLdQoS2xg2aQDG5OnfwLImpLxZql6tJBKAgFO3TNFKqOcSpaqBDBYkkqDkXEQqkIBUmHLJlK9LYWqiYdQvOjYPM65AZqvIZ7k9v0hW8733se7jkv57tgI4EhuCNICvYEVYHarKrlkbQ8Dbs97SDGBN8FRUGtA4Dmqlmeu4LRVgA+wVNBycPN/1eHgscCnx3IE2vBaUOchJlrhhjt0pdorpLgJtSPww/kgJCjS+S9doHLPcAYcN5p10ogQNVbkAAwYgD3gX6nXfnxcVLBIL3Ly0RyOYdZbKl+4B5WVB2f66upKUlSIZ/Xy5kZvQ6F9Lvzu7KDoNIOSEM/9/eVmJ7Wu2CwE5AybpuaQRoyt7e1ODmpjaGhtmA8A2kou7Wl55GI0gMDZwvS0Je1NcXDYWX6+hz59nR+6e11NRzmbiLBi+FhfjlY70H6/lW5XGYlFqN3aYlnpom/2yC1Wo0PCwv8mJ9nIpPhnItez0A2Uimy8TiRzU0uHh+77jeACriC/0vZdJqP0SjX1td5eHTUrk3ZAArAJbede6bJ+2iUK6urPDo4aBegoYIBfAYmsBtSbFSsVFicneVCMskD03TW1FoCPiG4rfoI5yjvbwcHddT523KyioJbCPyCbx4au62vwkq4YERnM6EdCq43H9Scuj+zxuxujK+LMCVBTK0CovogvaPT+68xBTec5slQPU3Lqk9wroanpqpYHm8sT9un5w+YJnqy6UwJgAAAAABJRU5ErkJggg=='}
        texto = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>

  <meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">
  <title>''' + self.tr('Estimate 3D Coordinates', self.str2HTML('Estimação de Coordenadas 3D')) + '''</title>
</head>
<body style="color: rgb(0, 0, 0); background-color: rgb(255, 255, 204);" alink="#000099" link="#000099" vlink="#990099">
<p class="MsoNormal" style="text-align: center;" align="center"><b><span style="font-size: 12pt; line-height: 107%;">''' + self.tr('ESTIMATE 3D COORDINATES', 'ESTIMA&Ccedil;&Atilde;O DE COORDENADAS 3D') + '''<o:p></o:p></span></b></p>
<p class="MsoNormal" style="text-align: center;" align="center"><i>''' + self.tr('Minimum Distance Method', 'M&eacute;todo das Dist&acirc;ncias M&iacute;nimas') + '''</i></p>
<p class="MsoNormal" style="text-align: center;" align="center"><b><u>''' + self.tr('REPORT','RELAT&Oacute;RIO') + '''<o:p></o:p></u></b></p>
<div>
<table style="text-align: center; width: 100%;" border="1" cellpadding="0" cellspacing="0">
  <tbody>
    <tr>
      <td width="50%"><b>''' + self.tr('Inputs', 'Dados de Entrada') + '''</b></td>
      <td width="50%"><b>'''+ self.tr('Adjustment','Ajustamento') + '''</b></td>
    </tr>
    <tr>
      <td style="text-align:  center;">
      <p class="MsoNormal" style="text-align: center;" align="center"><span style="font-style: italic;">''' + self.tr('Coordinates of the Optical Centers','Coordenadas dos Centros &Oacute;pticos')+ '''</span><o:p></o:p></p>
      <div align="center">
      <table class="MsoTableGrid" style="border: medium none ; border-collapse: collapse;" border="0" cellpadding="0" cellspacing="0">
        <tbody>
          [tabela 1]
        </tbody>
      </table>
      </div>
      <p class="MsoNormal" style="text-align: center;" align="center"><span style="font-style: italic;"></span></p>
      <p class="MsoNormal" style="text-align: center;" align="center"><span style="font-style: italic;">''' + self.tr('Azimuths','Azimutes') + '''</span><o:p></o:p></p>
      <div align="center">
      <table class="MsoTableGrid" style="border: medium none ; border-collapse: collapse;" border="0" cellpadding="0" cellspacing="0">
        <tbody>
          [tabela 2]
        </tbody>
      </table>
      </div>
      <p class="MsoNormal" style="text-align: center;" align="center"><span style="font-style: italic;"></span></p>
      <p class="MsoNormal" style="text-align: center;" align="center"><span style="font-style: italic;">''' + self.tr('Zenith Angles', '&Acirc;ngulos Zenitais') + '''</span><o:p></o:p></p>
      <div align="center">
      <table class="MsoTableGrid" style="border: medium none ; border-collapse: collapse;" border="0" cellpadding="0" cellspacing="0">
        <tbody>
          [tabela 3]
        </tbody>
      </table>
        <p class="MsoNormal" style="text-align: center;" align="center"><span style="font-style: italic;">''' + self.tr('Weight Matrix'+self.str2HTML('*'),'Matriz Peso'+self.str2HTML('*')) + ''': [PESO]</span><o:p></o:p></p>
      </div>
      </td>
      <td>
      <p class="MsoNormal" style="text-align: center;" align="center"><o:p>&nbsp;</o:p><span style="font-style: italic;">'''+ self.tr('Residuals (V)', 'Res&iacute;duos (V)') + '''</span><o:p></o:p></p>
      <div align="center">
      <table class="MsoTableGrid" style="border: medium none ; border-collapse: collapse;" border="1" cellpadding="0" cellspacing="0">
        <tbody>
        <tr style="">
            <td
 style="border: 1pt solid windowtext; padding: 0cm 5.4pt; width: 39.3pt;"
 valign="top" width="52">
            <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><i>'''+self.tr('Station', self.str2HTML('Estação')) + '''</i><o:p></o:p></p>
            </td>
            <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 46.05pt;"
 valign="top" width="61">
            <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><i>V_X</i><o:p></o:p></p>
            </td>
            <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 46.05pt;"
 valign="top" width="61">
            <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><i>V_Y</i><o:p></o:p></p>
            </td>
            <td
 style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 46.05pt;"
 valign="top" width="61">
            <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center"><i>V_Z</i><o:p></o:p></p>
            </td>
          </tr>
          [tabela 4]
        </tbody>
      </table>
      </div>
      <p class="MsoNormal" style="text-align: center;" align="center"><span style="font-style: italic;">''' + self.tr('Posteriori Variance', 'Vari&acirc;ncia a posteriori') + ''' &nbsp;</span>[VAR]<o:p></o:p></p>
      <p class="MsoNormal" style="text-align: center;" align="center"><span style="font-style: italic;">''' + self.tr(self.str2HTML('Adjusted Coordinates, Slant Ranges and Precisions**'), self.str2HTML('Coordenas Ajustados, Distâncias e Precis&otilde;es**')) + '''</span><o:p></o:p></p>
      <div align="center">
      <table class="MsoTableGrid" style="border: medium none ; width: 100.7pt; border-collapse: collapse;" border="1" cellpadding="0" cellspacing="0" width="134">
        <tbody>
          <tr style="">
            <td style="border: 1pt solid windowtext; padding: 0cm 5.4pt; width: 38.9pt;" valign="top" width="52">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">X<o:p></o:p></p>
            </td>
            <td style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 28.75pt;" valign="top" width="38">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">[X]<o:p></o:p></p>

            </td>

            <td style="border-style: solid solid solid none; border-color: windowtext windowtext windowtext -moz-use-text-color; border-width: 1pt 1pt 1pt medium; padding: 0cm 5.4pt; width: 33.05pt;" valign="top" width="44">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">[sX]<o:p></o:p></p>

            </td>

          </tr>

          <tr style="">

            <td style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 38.9pt;" valign="top" width="52">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">Y<o:p></o:p></p>

            </td>

            <td style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 28.75pt;" valign="top" width="38">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">[Y]<o:p></o:p></p>

            </td>

            <td style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 33.05pt;" valign="top" width="44">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">[sY]<o:p></o:p></p>

            </td>

          </tr>

          <tr style="">

            <td style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 38.9pt;" valign="top" width="52">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">Z<o:p></o:p></p>

            </td>

            <td style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 28.75pt;" valign="top" width="38">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">[Z]<o:p></o:p></p>

            </td>

            <td style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 33.05pt;" valign="top" width="44">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">[sZ]<o:p></o:p></p>

            </td>
          </tr>
        [SLANT_RANGE]
        </tbody>
      </table>
      </br>
      </div>
      </td>
    </tr>

  </tbody>
</table>
<p class="MsoNormal" style="text-align: left;" align="left"><i><span style="font-size: 10pt; line-height: 100%; color: rgb(127, 127, 127);">''' + self.tr(self.str2HTML('*')+'The inverse of the distances to the diagonal of the Weight Matrix is considered.', self.str2HTML('*')+'&Eacute; considerado o inverso das dist&acirc;ncias para a diagonal da Matriz Peso.') + '''
</br>''' + self.tr(self.str2HTML('**The unit of measurement of the adjusted coordinates is the same as the input coordinates.'), self.str2HTML('**A unidade de medida das coordenadas ajustadas é a mesma da coordenadas de entrada.')) + '''<o:p></o:p></span></i></p>
</div>

<footer">
<p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: right;" align="right"><b>''' + self.tr('Leandro Franca', self.str2HTML('Leandro França')) + '''
</br>''' + self.tr('Cartographic Engineer', 'Eng. Cart&oacute;grafo') + '''<o:p></o:p></b></p>
</br>
<div align="right">
<table style="text-align: right;" border="0"
 cellpadding="2" cellspacing="2">
  <tbody>
    <tr>
      <td><a target="_blank" rel="noopener noreferrer" href="https://www.udemy.com/user/leandro-luiz-silva-de-franca/">
      <img title="Udemy" style="border: 0px solid ; width: 28px; height: 28px;" alt="udemy"
       src="data:image/png;base64,'''+dic_color['udemy']+'''">
       </a>
      </td>
      <td><a target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/GEOCAPT/">
      <img title="Facebook" style="border: 0px solid ; width: 28px; height: 28px;" alt="facebook"
       src="data:image/png;base64,'''+dic_color['face']+'''">
       </a>
      </td>
      <td><a target="_blank" rel="noopener noreferrer" href="https://www.youtube.com/channel/UCLrewDGciytcBG9r0OxTW2w">
      <img title="Youtube" style="border: 0px solid ; width: 28px; height: 28px;" alt="youtube"
       src="data:image/png;base64,'''+dic_color['youtube']+'''">
       </a>
      </td>
      <td><a target="_blank" rel="noopener noreferrer" href="https://www.researchgate.net/profile/Leandro_Franca2">
      <img title="ResearchGate" style="border: 0px solid ; width: 28px; height: 28px;" alt="RG"
       src="data:image/png;base64,'''+dic_color['RG']+'''">
       </a>
      </td>
      <td><a target="_blank" rel="noopener noreferrer" href="https://github.com/LEOXINGU">
      <img title="GitHub" style="border: 0px solid ; width: 28px; height: 28px;" alt="github"
       src="data:image/png;base64,'''+dic_color['github']+'''">
       </a>
      </td>
      <td><a target="_blank" rel="noopener noreferrer" href="https://www.linkedin.com/in/leandro-fran%C3%A7a-93093714b/">
      <img title="Linkedin" style="border: 0px solid ; width: 28px; height: 28px;" alt="linkedin"
       src="data:image/png;base64,'''+dic_color['linkedin']+'''">
       </a>
      </td>
      <td><a target="_blank" rel="noopener noreferrer" href="http://lattes.cnpq.br/8559852745183879">
      <img title="Lattes" style="border: 0px solid ; width: 28px; height: 28px;" alt="lattes"
       src="data:image/png;base64,'''+dic_color['lattes']+'''">
       </a>
      </td>
    </tr>
  </tbody>
</table>
</div>

<o:p></o:p></b></p>
</footer>
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
            <td style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 39.3pt;"
 valign="top" width="52">
            <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[STATION]<o:p></o:p></p>
            </td>
            <td style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 46.05pt;"
 valign="top" width="61">
            <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[V_x]<o:p></o:p></p>
            </td>
            <td
 style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 46.05pt;"
 valign="top" width="61">
            <p class="MsoNormal"
 style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;"
 align="center">[V_y]<o:p></o:p></p>
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
        linha_slant_range = '''<tr style="">

            <td style="border-style: none solid solid; border-color: -moz-use-text-color windowtext windowtext; border-width: medium 1pt 1pt; padding: 0cm 5.4pt; width: 38.9pt;" valign="top" width="52">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">t[VISADA]<o:p></o:p></p>

            </td>

            <td style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 28.75pt;" valign="top" width="38">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">[tn]<o:p></o:p></p>

            </td>

            <td style="border-style: none solid solid none; border-color: -moz-use-text-color windowtext windowtext -moz-use-text-color; border-width: medium 1pt 1pt medium; padding: 0cm 5.4pt; width: 33.05pt;" valign="top" width="44">
            <p class="MsoNormal" style="margin-bottom: 0.0001pt; text-align: center; line-height: normal;" align="center">[s_tn]<o:p></o:p></p>

            </td>
          </tr>'''
        linhas_s_r = ''
        for k, t in enumerate(slant_range):
            tableRowN = linha_slant_range
            linhas_s_r += tableRowN.replace('[VISADA]', str(k+1)).replace('[tn]', str(t)).replace('[s_tn]', str(s_t[k]))
        
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
                         '[STATION]' : str(k+1),
                         }
            for item in itens:
                tableRowN = tableRowN.replace(item, itens[item])
            table4 += tableRowN
        
        texto = texto.replace('[tabela 1]', table1).replace('[tabela 2]', table2).replace('[tabela 3]', table3).replace('[tabela 4]', table4)
        texto = texto.replace('[PESO]', self.tr('Yes', 'Sim') if usar_peso else self.tr('No', self.str2HTML('Não')))
        texto = texto.replace('[VAR]', VAR)
        texto = texto.replace('[X]', str(x)).replace('[Y]', str(y)).replace('[Z]', str(z)).replace('[sX]', str(s_x)).replace('[sY]', str(s_y)).replace('[sZ]', str(s_z))
        texto = texto.replace('[SLANT_RANGE]', linhas_s_r)
        # Exportar HTML
        arq = open(html_output, 'w')
        arq.write(texto)
        arq.close()
        
        feedback.pushInfo(self.tr('Operation completed successfully!', 'Operação finalizada com sucesso!'))
        feedback.pushInfo(self.tr('Leandro França - Eng Cart', 'Leandro Franca - Cartographic Engineer'))
        
        Carregar = self.parameterAsBool( 
            parameters,
            self.OPEN,
            context
        )
        
        self.CAMINHO = output
        self.CARREGAR = Carregar
        
        return {self.OUTPUT: output,
                self.HTML: html_output}
    
    
    # Carregamento de arquivo de saída
    CAMINHO = ''
    CARREGAR = True
    def postProcessAlgorithm(self, context, feedback):
        if self.CARREGAR:
            vlayer = QgsVectorLayer(self.CAMINHO, self.tr('Adjusted 3D Coordinates', 'Coordenadas 3D Ajustadas'), "ogr")
            QgsProject.instance().addMapLayer(vlayer)
        return {}
