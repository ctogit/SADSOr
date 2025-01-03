# -*- coding: utf-8 -*-
# !/home/pi/SADSOr
# by CTo 03/2018
# torrescristian@outlook.com
"""
adjust.py
 
Recibe parametros de MS por bluetooth desde uC PIC con modulo HC-05 a 115200 Baudios
Se almacenan los datos en un archivo de texto y se grafican.

Formación de la Trama de datos:
|Byte0|Byte1||Byte2|Byte3||Byte4|Byte5||Byte6|Byte7||Byte8|Byte9||Byte10|
| Inicio Tr ||   Nº Tr   ||    Vms    ||    Ims    ||    rpm    ||  CS  |
|   F0F0    |
"""

import matplotlib as mpl
import os
import serial
import math
import pylab
import matplotlib.pyplot as plt
import datetime as dt
from time import time, gmtime, strftime, sleep
from datetime import datetime, timedelta
import sys
import numpy as np
from os import system
from scipy.signal import butter, lfilter, freqz
import logger
#import pandas as pd
from filtrar import*


###################################################################################################
# Nombre función: RecibirDatos()
# Entradas: no
# Salidas: frame - tramas de datos o tiempo
# Propósito: escucha el puerto serie permanentemente 
###################################################################################################

def RecibirDatos():
    global checksum1
    global bandera
    global start
    
    addr = '/dev/rfcomm0'		                    # Puerto serie Raspberry Pi conectada a BT 
    baud = 115200
    #port = serial.Serial(addr,baud,timeout = 0.05)
    port = serial.Serial(addr,baud,timeout = 0.5)

    frame=[]
    checksum1 = 0
    s = 0
    while s!=240:         # 240 = 0xF0: Datos / 250 = 0xFA: Tiempo
        try:
            s=port.read(1)
            s=ord(s)
        except:
            if bandera == 1:
                start = 0
            
    bandera = 1

    s = ord(port.read(1))
    if s==240:
        """
        Formacion de la Trama:
        |Byte0|Byte1||Byte2|Byte3||Byte4|Byte5||Byte6|Byte7||Byte8|
        |   Nº Tr   ||    Vms    ||    Ims    ||    rpm    || CS  |
        """
        for x in range(0, 9):                       # 8 bytes de datos mas 1 byte CS
            s = ord(port.read(1))
            frame.append(s)
            if x != 8: 
                checksum1 = checksum1 + s
    while checksum1 >= 256:                         # truncamos el checksum a 8 bits solamente
        checksum1 = checksum1 - 256
    #print frame
    return frame

def recordForAdjust(ms):
    global bandera
    global start
    global timeFlag
    global equipo
  
    bandera = 0                                     # bandera y start son variables globales que se usan para
    start = 1                                       # permtir que el programa quede a la espera del gas-on al inicio
                                                    # y salga del while con el gas off  
    i=0
    ts = 0.005                                      # tiempo de muestreo en uC [segundos]
    aux = 0                                         # cuenta la cantidad de veces que desborda el nº trama
    n_max = 60000
            
    fecha, hora = str(dt.datetime.utcnow()).split(' ')
    ano, mes, dia = fecha.split('-')
    h, m, s = hora.split(':')
    s, trash = s.split('.')
    fname = "MS"+str(ms)+"_datosADC_"+ano+mes+dia+"_"+h+m+s
    fmode = 'a+b'
    outf = open('data/'+fname,fmode)

    logger.critical(" Recibiendo y guardando datos en: %s.txt..."%fname)
                
    while start == 1:                           # start se hace 0 si no se reciben tramas por 50 ms        
        try:
            datos = RecibirDatos()                
            n = datos[0]*256+datos[1]
                            
            seg = (n+(n_max+1)*aux)*ts          # n desborda en 60000 pero t debe seguir contando...
            if n == n_max:
                aux += 1

            Vms = datos[2]*256+datos[3]
            Ims = datos[4]*256+datos[5]
            rpm = datos[6]*256+datos[7]
                        
            #Checksum 
            checksum0 = datos[8]

            if checksum0 == checksum1:
                outf.write("%s;%s;%s;%s;%s\n"%(seg,n,Vms,Ims,rpm))
                outf.flush()
            else:
                logger.error(" Error en checksum, se desecha trama")

        except Exception as e:
            if str(e) != "list index out of range":
                logger.error(" Error en la comunicación, %s"%e)
            pass
    return fname

def graphForAdjust(archivo, guardar, ms):
    try:
        mpl.style.use('ggplot')                     # Estilo del grafico

        #### Cambiar archivo de datos que se quiera graficar ###
        registro="data/"+archivo
        if registro == "data/":
            registro="data/datos_201708_101544"
        ########################################################
            
        ##############
        #MAIN PROGRAM#
        ##############

        h, lines = read_spreadsheet(registro,csv_dialect=CToDialect, header_size=1) #tengo que sacrificar 2 lineas de datos porque aveces los datos desde V1D1_IF estan vacios y frena el script
        ####
        Date_list=[]
        Time_list =[]
        V_list=[]
        Vmin_list=[]
        I_list=[]
        Imin_list=[]
        Imax_list=[]
        RPM_list=[]
        ####
        #ms=47
        #guardar = "Si"

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
            
        for x in range(0,len(lines)-1):
            Time_list.append(float(lines[x][0]))
            if float(lines[x][2]) >= 4096.0:
                lines[x][2] = 0
            V_list.append(float(lines[x][2]))
            if float(lines[x][3]) >= 4096.0:
                lines[x][3] = 0
            I_list.append(float(lines[x][3]))
            print(archivo[2:4])
            if (float(archivo[2:4]) == 32.0) and (float(lines[x][4]) >= 4096.0):
                lines[x][4] = 0
            RPM_list.append(float(lines[x][4]))
            if V_list[x] > 3 and Xmin == 0:                 #Busca primer aumento de tension para establecer el inicio del grafico
                Xmin = Time_list[x] - 0.5   
            if RPM_list[x] >= 0.7:                            #Busca valor maximo de RPM
                aux = 1
            if aux == 1 and RPM_list[x] <= 0.7:
                aux = 0
                Xmax = x*0.005 + 0.5                        #Busca valor X maximo de RPM 
            
        Xmin = 0
        Xmax = 25

        #########################################################################
        #                       Filtrado Digital Tension                        #
        #########################################################################

        order = 4
        #order = 9
        fs = 200       # sample rate, Hz
        #cutoff = 25  # desired cutoff frequency of the filter, Hz
        cutoff = 10  # desired cutoff frequency of the filter, Hz

        #V_list = butter_lowpass_filter(V_list, cutoff, fs, order)

        #########################################################################
        #                       Filtrado Digital Corriente                      #
        #########################################################################

        order = 2
        #order = 9
        fs = 200       # sample rate, Hz
        cutoff = 16  # desired cutoff frequency of the filter, Hz
        #cutoff = 7  # desired cutoff frequency of the filter, Hz

        #I_list = butter_lowpass_filter(I_list, cutoff, fs, order)

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
                PlotName= "Registro para Ajuste "+d1+d2+"/"+m1+m2+"/"+"20"+a3+a4+" "+h1+h2+":"+min1+min2+" hs "+str(msID)
            elif guardar == "No":
                PlotName= "Registro para Ajuste "+d1+d2+"/"+m1+m2+"/"+"20"+a3+a4+" "+h1+h2+":"+min1+min2+" hs "+str(msID)
        else:
            PlotName= "Registro Soldadura Orbital (tipo)"

        #################################################################################
        #                               PLOTS                                           #
        #################################################################################
        colorR = 'k'
        colorV = 'r'
        colorI = 'b'
        # Make Plots: period after line indicate that this last will be updated in time.
        pylab.plt.figure(figsize=(9.8,5))
        #pylab.plt.figure(figsize=(24,14))       # monitor 24in

        #################################################################################
        #                          V vs. Time Plot
        #################################################################################
        ax1 = plt.subplot(3,1,1)
        #ax1.figure.figimage(logo, 1650, 770, alpha=1, zorder=-1)
        pylab.title(PlotName, fontsize=14)
        pylab.plot(Time_list, V_list, colorV)
        pylab.plt.ylim(ymin=0)
        pylab.plt.ylim(ymax=3000)
        pylab.plt.xlim(xmin=Xmin)
        pylab.plt.xlim(xmax=Xmax)
        pylab.xticks(rotation=0, fontsize = 8)
        pylab.yticks(rotation=0, fontsize = 8)
        pylab.ylabel("ADC_V", color = colorR, fontsize = 10)

        pylab.grid(True)

        #################################################################################
        #                          I vs. Time Plot
        #################################################################################
        ax2 = pylab.subplot(3,1,2)
        pylab.plot(Time_list, I_list, colorI)
        pylab.plt.ylim(ymin=0)
        pylab.plt.ylim(ymax=1100)
        pylab.plt.xlim(xmin=Xmin)
        pylab.plt.xlim(xmax=Xmax)
        pylab.xticks(rotation=0, fontsize = 8)
        pylab.yticks(rotation=0, fontsize = 8)
        pylab.ylabel("ADC_I", color = colorR, fontsize = 10)
        pylab.grid(True)
        #################################################################################
        #                          RPM vs. Time Plot
        #################################################################################
        #  RPMmax = 1700
        #  RPMmin = 0
        ax3 = pylab.subplot(3,1,3)
        pylab.plot(Time_list, RPM_list, colorR)
        pylab.plt.xlim(xmin=Xmin)
        pylab.plt.xlim(xmax=Xmax)
        pylab.xticks(rotation=0, fontsize = 8)
        pylab.yticks(rotation=0, fontsize = 8)
        if float(archivo[2:4]) == 32.0:
            pylab.ylabel("ADC_T", color = colorR, fontsize = 10)
        else:
            pylab.ylabel("f", color = colorR, fontsize = 10)
        pylab.xlabel("Tiempo [seg]", fontsize = 10)
        pylab.grid(True)
        #################################################################################
        #

        if guardar == "Si":
            logger.info(" Generando gráfico: %s.pdf"%archivo)
            pylab.savefig("graficos/"+archivo+".pdf", dpi=600)
        elif guardar == "No":
            logger.info(" Se re-graficó archivo histórico: %s.pdf"%archivo)

        ###

        ShowGraphs= True

        if ShowGraphs:
            pylab.show()
            
    except Exception as e:
        logger.error(" Hubo un error al graficar, %s"%e)
        pass
