# -*- coding: utf-8 -*-
# !/home/cto/SADSOr
# by CTo 12/2024
# torrescristian@outlook.com
###################################################################################################
# Nombre función: RegistrarYalmacenar()
# Entradas: ms - número máquina de soldar
#           tipoCab: tipo de cabezal
# Salidas: none
# Propósito: escucha el puerto serie permanentemente 
###################################################################################################
""" 
Recibe parametros de MS por bluetooth desde uC PIC con modulo HC-05 a 115200 Baudios
Se almacenan los datos en un archivo de texto y se grafican.

Formación de la Trama de datos:
|Byte0|Byte1||Byte2|Byte3||Byte4|Byte5||Byte6|Byte7||Byte8|Byte9||Byte10|
| Inicio Tr ||   Nº Tr   ||    Vms    ||    Ims    ||    rpm    ||  CS  |
|   F0F0    |
"""

import os
import serial
import math
import matplotlib.pylab
import matplotlib.pyplot
import numpy
import time
import datetime as dt
from datetime import datetime, timedelta
import sys
from os import system
from scipy.signal import butter, lfilter, freqz
import logger
import csv
from depurador import *
global start     

def registrarYalmacenar(ms, tipoCab):
    global checksum1
    global bandera
    global start
    global timeFlag
    global equipo
    global cabezal
    global addr
    global baud
    global port
    
    path = "/home/cto/SADSOr/"
    
    buffer = []
    header = []
    tamanio_buffer = 25

    #os.system('sudo rfcomm connect /dev/rfcomm0 98:D3:32:20:A1:61 1') 
    
    bandera = 0                                     # bandera y start son variables globales que se usan para
    start = 1                                       # permtir que el programa quede a la espera del gas-on al inicio
                                                    # y salga del while con el gas off  
    i=0
    ts = 0.005                                      # tiempo de muestreo en uC [segundos]
    aux = 0                                         # cuenta la cantidad de veces que desborda el nº trama
    n_max = 60000
    
    frame=[]
    raw_frame=[]
    checksum1 = 0
     
    ###############################################################################
    #          RECEPCIÓN DE DATOS VIA RS232 A TRAVÉS DE BLUETOOTH                 #
    ###############################################################################
            
    fecha, hora = str(dt.datetime.utcnow()).split(' ')
    ano, mes, dia = fecha.split('-')
    h, m, s = hora.split(':')
    s, trash = s.split('.')
    fname = "MS"+str(ms)+"_datos_"+ano+mes+dia+"_"+h+m+s
    #fmode = 'a+b' # trabaja con datos binarios
    fmode = 'a' # trabaja con cadenas de texto
    #outf = open('data/'+fname, fmode)

    depurador(1, "REGISTRAR", "Inicia")
    logger.critical(f"Recibiendo y guardando datos en: {fname} ...\r")
    
    addr = '/dev/rfcomm0'		                            # Puerto serie Raspberry Pi conectada a BT 
    baud = 115200
                
    while(start == 1):                                      # start se hace 0 si no se reciben tramas en un cierto tiempo.  
        n = 0
        seg = 0 
        Vms = 0.0
        Ims = 0.0
        rpm = 0.0 
        no_hay_mas_tramas = 0
            
        with serial.Serial(addr,baud,timeout = 1,rtscts=True) as port:
            raw_frame = [240, 240] 
            try:
                while raw_frame[0] == 240 and raw_frame[1] == 240:                  # 240 = 0xF0: Datos / 250 = 0xFA: Tiempo
                    if port.in_waiting >= 11:               # Verifica si hay suficiente data en el buffer
                        raw_frame = port.read(11)           # Captura los 11 bytes de una trama.
                        no_hay_mas_tramas = 0
                         
                        depurador(3, "REGISTRAR", ",".join(map(str, raw_frame)))      
                                    
                        datos = raw_frame[2:11]           
                            
                        n = datos[0]*256+datos[1]
                            
                        seg = int((n+(n_max+1)*aux)*ts*1000)/1000          # n desborda en 60000 pero t debe seguir contando...
                        if n == n_max:
                            aux += 1
                        ###################################################################################################################
                        #                                                ESCALADO  
                        ###################################################################################################################
                        if ms == 50:
                            Vms = (datos[2]*256+datos[3])*0.0074 - 0.1804       # Ajustado 07/03/2018 en base a SPC-DEEE-IN-202.
                            Ims = (datos[4]*256+datos[5])*0.0737 - 1.9056       # Ajustado 09/03/2018 en base a SPC-DEEE-IN-202.
                                      
                        ######################################################
                        if ms == 47:
                            Vms = ((datos[2]*256+datos[3])*0.0073851 - 0.4617) # MPo, JMo, CTo cal 29/12/17 (ver informe GSPC-SEOE-001-18)
                            Ims = ((datos[4]*256+datos[5])*0.0736 - 1.2659) # MPo, JMo, CTo cal 11/01/18 (ver informe GSPC-SEOE-001-18)
                                      
                        ######################################################
                        if ms == 49:
                            Vms = ((datos[2]*256+datos[3])*0.00743 - 0.14936) # GPe, CTo adj 29/04/19 for SADSOr U2
                            Ims = ((datos[4]*256+datos[5])*0.07393 - 1.22548) # GPe, CTo adj 29/04/19 for SADSOr U2
                                    
                        ######################################################
                        if ms == 32:
                            Vms = (datos[2]*256+datos[3])*0.0113511852952 - 0.678440206201  # Ajustado 31/03/2018 en base a SPC-DEEE-IN-202.
                            Ims = (datos[4]*256+datos[5])*0.0696332656845 - 4.00305149578   # Ajustado 31/03/2018 en base a SPC-DEEE-IN-202.

                        ###################################################################################################################
                        if ms == 99:
                            Vms = 0
                            Ims = 0
                            rpm = 0
                            #Vms = (datos[2]*256+datos[3])*0.0074 - 0.1804       # Módulo de prueba, no hace falta ajustar.
                            #Ims = (datos[4]*256+datos[5])*0.0737 - 1.9056       # Módulo de prueba, no hace falta ajustar.
                        else:
                            if tipoCab == 810:
                                rpm = (datos[6]*256+datos[7])/100.0 #
                            if tipoCab == 805:
                                rpm = ((datos[6]*256+datos[7])/100.0)*(15311.0/8951.0) # acorde a mediciones by CTo 20190521
                            if tipoCab == 10:
                                rpm = (datos[6]*256+datos[7])*0.00226165291177 - 0.195191444845 # Ajustado 31/03/2018 en base a SPC-DEEE-IN-202.
                        ######################################################
                                        
                        if Vms >= 35:
                            Vms = 0
                                        
                        if Ims >= 340:
                            Ims = 0 
                                                
                        #Checksum 
                        checksum0 = datos[8]
                        checksum1 = sum(datos[0:7])
                        while checksum1 >= 256:                         # truncamos el checksum a 8 bits solamente
                            checksum1 = checksum1 - 256
                            
                        #print(seg, n, Vms, Ims, rpm, checksum1, checksum0, "\r")

                        if checksum0 == checksum1:
                            buffer.append([seg, n, Vms, Ims, rpm])
                            if len(buffer) >= tamanio_buffer:
                                with open(path+'data/'+fname, fmode, newline="") as file:
                                    escritor_csv = csv.writer(file, delimiter=';')
                                    escritor_csv.writerows(buffer)
                                buffer.clear()
                        elif checksum0 != checksum1:
                            depurador(3, "REGISTRAR", f"Checksum error: cs0={checksum0} - cs1={checksum1}, se desecha trama: {n}") 
                            #logger.error(f" Error en checksum, se desecha trama: {n}")
                            
                    else:
                        no_hay_mas_tramas += 1
                        if no_hay_mas_tramas >= 100000:
                            depurador(1, "REGISTRAR", "No hay más tramas")
                            start = 0
                            break


            except Exception as e:
                depurador(2, "REGISTRAR", f"Error en bucle de recepción: {e}")
                pass
    depurador(1, "REGISTRAR", "Finaliza") 
    return fname
                       
#if __name__ == "__registrarYalmacenar__":
    #registrarYalmacenar()
		
