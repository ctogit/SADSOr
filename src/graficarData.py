# -*- coding: utf-8 -*-
"""
GraficarDatosHistoricos.py

- Este script grafica los datos almacenados en el archivo "Registro"

Util para graficar algun archivo que ya haya sido graficado previamente
y no basta con el .pdf creado sino que se necesita hacer algun zoom o
detallar alguna parte.

by CTo 2017/08
"""

import matplotlib as mpl
#import pandas as pd
import numpy as np
from filtrar import*
import csv
#import pylab
import sys
import datetime as dt
import matplotlib.pyplot as plt
import logger
import traceback
from depurador import *

def graficar(archivo, guardar, ms):
    try:
        depurador(1, "GRAFICAR", f"Inicia con archivo: {archivo}")
        path = "/home/cto/SADSOr/"
        mpl.use('GTK3Agg') # Backend compatible con GTK3.
        mpl.style.use('classic')                     # Estilo del grafico

        #### Cambiar archivo de datos que se quiera graficar ###
        registro="/home/cto/SADSOr/data/"+archivo
        if registro == path+"data/":
            registro=path+"data/datos_201708_101544"
        ########################################################
            
        ##############
        #MAIN PROGRAM#
        ##############
        Date_list=[]
        Time_list =[]
        V_list=[]
        Vmin_list=[]
        I_list=[]
        Imin_list=[]
        Imax_list=[]
        RPM_list=[]
        ####

        Xmin = 0
        Xmax = 0
        Vmax = 0
        Vmin = 0 
        Imax = 0
        Rmax = 0
        nImax = 0
        Xvmax = 0   
        Xvmin = 0
        aux = 0

        with open(registro, newline='', encoding='utf-8') as csvfile:
            lector = csv.reader(csvfile, delimiter=';')
            # ignorar encabezados
            next(lector)
            lines = list(lector) #convierte el iterador en una lista
            ####
        
            for x, fila in enumerate(lines):
                # Extraer columnas necesarias
                Time_list.append(float(lines[x][0]))
                V_list.append(float(lines[x][2]))
                I_list.append(float(lines[x][3]))  
                RPM_list.append(float(lines[x][4]))
                if V_list[x] > 3 and Xmin == 0:                 #Busca primer aumento de tension para establecer el inicio del grafico
                    Xmin = Time_list[x] - 0.5   
                if RPM_list[x] >= 0.7:                            #Busca valor maximo de RPM
                    aux = 1
                if aux == 1 and RPM_list[x] <= 0.7:
                    aux = 0
                    Xmax = x*0.005 + 0.5                        #Busca valor X maximo de RPM  
        #Vmax = max(V_list)+0.5
        Vmax = 11.5
        Vmin = 6.5
        
        #RPMmax = max(RPM_list)+0.5
        RPMmax = 17
        RPMmin = 0
        if Xmin >= Xmax:  
            Xmin = 0
            Xmax = 45

        #########################################################################
        #                       Filtrado Digital Tension                        #
        #########################################################################

        order = 1
        #order = 4      # hasta 08/05/2021
        fs = 200        # sample rate, Hz
        #cutoff = 10    # hasta 08/05/2021
        cutoff = 1      # desired cutoff frequency of the filter, Hz

        V_list = butter_lowpass_filter(V_list, cutoff, fs, order)

        #########################################################################
        #                       Filtrado Digital Corriente                      #
        #########################################################################

        order = 2
        #order = 9
        fs = 200       # sample rate, Hz
        cutoff = 16  # desired cutoff frequency of the filter, Hz
        #cutoff = 7  # desired cutoff frequency of the filter, Hz

        I_list = butter_lowpass_filter(I_list, cutoff, fs, order)
        Imax = max(I_list)+0.5
        Imin = 0

        #Vmin = min(V_list[Xvmin:Xvmax]) - 0.5
        #Vmax = max(V_list[Xvmin:Xvmax]) + 0.5

        #########################################################################
        #                       Filtrado Digital Travel                         #
        #########################################################################

        order = 3
        fs = 200       # sample rate, Hz
        cutoff = 20  # desired cutoff frequency of the filter, Hz
        #RPM_list = butter_lowpass_filter(RPM_list, cutoff, fs, order)

        ##########################################################################

        if archivo != "defaultFile":
            trash, trash, fecha, hora = archivo.split("_")

            d1 = fecha[6]
            d2 = fecha[7]
            m1 = fecha[4]
            m2 = fecha[5]
            a3 = fecha[2]
            a4 = fecha[3]
        
            h1 = hora[0]
            h2 = hora[1]
            min1 = hora[2]
            min2 = hora[3]

            msID = archivo[0:4]
     
            if guardar == "Si":
                PlotName= "Registro Soldadura Orbital "+d1+d2+"/"+m1+m2+"/"+"20"+a3+a4+" "+h1+h2+":"+min1+min2+" hs "+str(msID)
            elif guardar == "No":
                PlotName= "Registro Historico del dia "+d1+d2+"/"+m1+m2+"/"+"20"+a3+a4+" "+h1+h2+":"+min1+min2+" hs "+str(msID)
        else:
            PlotName= "Registro Soldadura Orbital (tipo)"

        #################################################################################
        #                               PLOTS                                           #
        #################################################################################
        colorR = 'k'
        colorV = 'r'
        colorI = 'b'
        # Make Plots: period after line indicate that this last will be updated in time.
        plt.figure(figsize=(9.8,5))
        #plt.figure(figsize=(24,14))       # monitor 24in

        #################################################################################
        #                          V vs. Time Plot
        #################################################################################
        ax1 = plt.subplot(3,1,1)
        #ax1.figure.figimage(logo, 1650, 770, alpha=1, zorder=-1)
        plt.title(PlotName, fontsize=14)
        plt.plot(Time_list, V_list, colorV, linewidth=0.5)
        plt.ylim(ymin=Vmin)
        plt.ylim(ymax=Vmax)
        plt.xlim(xmin=Xmin)
        plt.xlim(xmax=Xmax)
        plt.xticks(rotation=0, fontsize = 8)
        plt.yticks([7, 8, 9, 10, 11], fontsize = 8)
        plt.ylabel("Tension [V]", color = colorR, fontsize = 10)

        plt.grid(True)

        #################################################################################
        #                          I vs. Time Plot
        #################################################################################
        ax2 = plt.subplot(3,1,2)
        plt.plot(Time_list, I_list, colorI, linewidth=0.5)
        plt.ylim(ymin=Imin)
        plt.ylim(ymax=Imax)
        plt.xlim(xmin=Xmin)
        plt.xlim(xmax=Xmax)
        plt.xticks(rotation=0, fontsize = 8)
        if Imax > 30:
            plt.yticks([0, 10, 20, 30], fontsize = 8)
        if Imax > 40:
            plt.yticks([0, 10, 20, 30, 40], fontsize = 8)
        if Imax > 50:
            plt.yticks([0, 10, 20, 30, 40, 50], fontsize = 8)
        if Imax > 60:
            plt.yticks([0, 10, 20, 30, 40, 50, 60], fontsize = 8)
        if Imax > 70:
            plt.yticks([0, 10, 20, 30, 40, 50, 60, 70], fontsize = 8)
            
        plt.ylabel("Corriente [A]", color = colorR, fontsize = 10)
        plt.grid(True)
        #################################################################################
        #                          RPM vs. Time Plot
        #################################################################################
        ax3 = plt.subplot(3,1,3)
        plt.plot(Time_list, RPM_list, colorR, linewidth=0.5)
        plt.ylim(ymin=RPMmin)
        plt.ylim(ymax=RPMmax)
        plt.xlim(xmin=Xmin)
        plt.xlim(xmax=Xmax)
        plt.yticks([0, 2, 4, 6, 8, 10, 12, 14, 16], fontsize = 8)
        plt.xticks(rotation=0, fontsize = 8)
        plt.ylabel("RPM", color = colorR, fontsize = 10)
        plt.xlabel("Tiempo [seg]", fontsize = 10)
        plt.grid(True)
        #################################################################################
        #

        if guardar == "Si":
            depurador(1, "GRAFICAR", f"Generando gráfico: {archivo}.pdf")
            logger.info(" Generando gráfico: %s.pdf"%archivo)
            plt.savefig(path+"graficos/"+archivo+".pdf", dpi=600)
        elif guardar == "No":
            depurador(1, "GRAFICAR", f"Se re-graficó archivo histórico: {archivo}.pdf")
            logger.info(" Se re-graficó archivo histórico: %s.pdf"%archivo)

        ###

        ShowGraphs= True

        if ShowGraphs:
            depurador(1, "GRAFICAR", "Por mostrar el gráfico")
            plt.show()
            
    except Exception as e:
        traceback.print_exc()
        depurador(1, "GRAFICAR", f"Hubo un error al graficar: {e}")
        logger.error(" Hubo un error al graficar, %s"%e)
        pass
