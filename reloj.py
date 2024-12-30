# -*- coding: utf-8 -*-
# !/home/pi/SADSOr
# by CTo 10/2017
# torrescristian@outlook.com

import os
import subprocess
import logger
import serial

###################################################################################################
# Nombre función: fechaYhora()
# Entradas: no
# Salidas: timeFlag
# Propósito: pregunta fecha y hora al uC y la actualiza en la RPi al inicar
#           la comunicación BT. Si el proceso fue correcto retorna 1 sino 0.
###################################################################################################

def fechaYhora():  
    timeFrame=[]
    cs_rpi = 0                                              # checksum calculado por RPi
    timeFlag = 0
    
    addr = '/dev/rfcomm0'		                    # Puerto serie Raspberry Pi conectada a BT 
    baud = 115200
    port = serial.Serial(addr,baud,timeout = 0.5)
    
    print("Entrando a fechaYHora \r")
    port.write(b'c')
    port.write(b'k')
    
    """
    Formación de la Trama de tiempo:
    |Byte0|Byte1||Byte2||Byte3||Byte4||Byte5||Byte6||Byte7||Byte8||Byte9||Byte10|
    | Inicio Tr || Año || Mes || Día ||hora || Min || Seg ||0x00 ||0x00 ||  CS  |
    |   FAFA    |
    """
    t = 0
    #try:
    if True:
        while t != 250:                         # 240 = 0xF0: Datos / 250 = 0xFA: Tiempo
            t_byte_literal = port.read(1)       # Leer 1 byte del puerto  
            try:
                t = t_byte_literal[0]               # Sería como una conversión de byte literal a decimal
            except:
                t = 0
                pass
        print(f"reloj 1 - 1er byte recibido = {t} \r")
        t_byte_literal = port.read(1)           # Leer 1 byte del puerto   
        t = t_byte_literal[0]   
        print(f"reloj 1 - 2do byte recibido = {t} \r")   
        
        if t == 250:
            print(f"reloj 2 - t = {t} \r")
            """
            Formacion de la Trama:
            |Byte0|Byte1|Byte2|Byte3|Byte4|Byte5|Byte6|Byte7|Byte8|
            | Año | Mes | Día |Hora | Min | Seg |0x00 |0x00 | CS  |
            """
            for x in range(0, 9):                       # 8 bytes de datos mas 1 byte CS
                t_byte_literal = port.read(1)
                t = t_byte_literal[0]
                print(f"reloj 3 - trama = {t} \r")
                timeFrame.append(t)
                if x != 8: 
                    cs_rpi = cs_rpi + t
        print(f"timeFrame: {timeFrame}")
        print("reloj 4 \r")
        while cs_rpi >= 256:                         # truncamos el checksum a 8 bits solamente
            cs_rpi = cs_rpi - 256

        ano = str(timeFrame[0])
        mes = int(timeFrame[1])
        if mes < 10:
            mes = str(0)+str(mes)
        else:
            mes = str(mes)
        dia = int(timeFrame[2])
        if dia < 10:
            dia = str(0)+str(dia)
        else:
            dia = str(dia)
        hora = int(timeFrame[3])
        if hora < 10:
            hora = str(0)+str(hora)
        else:
            hora = str(hora)
        minuto = int(timeFrame[4]) + 1              # sumamos 1 min porque la rpi se demora en actualizar
        if minuto < 10:
            minuto = str(0)+str(minuto)
        else:
            minuto = str(minuto)
        segundo = int(timeFrame[5])
        if segundo < 10:
            segundo = str(0)+str(segundo)
        else:
            segundo = str(segundo)
        cs_pic = timeFrame[8]
       
    #except Exception as e:
    else:
        print("reloj 6")
        print(e)
        cs_pic = 1
        
        pass
      
    #ano = str(24)
    #mes = str(12)
    #dia = str(11)
    #hora = str(0)
    #minuto = str(0)
    #segundo = str(0)

    if cs_pic == cs_rpi:
        #port.write("ok")
        os.system('sudo -S date -s "'+ano+mes+dia+' '+hora+':'+minuto+':'+segundo+'"')
        logger.info(" Se actualizó fecha y hora")
        timeFlag = 1
        
    else:                           # error log cada 1h aprox.
        timeFlag = 0
        
    return timeFlag

    
