# -*- coding: utf-8 -*-
# !/home/cto/SADSOr
# by CTo 03/2018
# torrescristian@outlook.com
#
# 22/05/2019
# Debido a la compra de nuevos cabezales serie 805 se tuvo que actualizar
# el software ya que el factor de conversion frecuencia a rpm es diferente
# entre 810 y 805.
# Se aprovecho para actualizar la interfaz, ahora el operador puede elegir
# ms y tipo de cabezal desde menus desplegables. Archivos modificados: sadsor.py,
# registrar.py y new_gui.glade.

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject
from registrar import registrarYalmacenar
from graficarData import *
from filtrar import *
from reloj import fechaYhora
import os
from os import system
import serial
import math
import pylab
import matplotlib.pyplot
import datetime as dt
from time import time, gmtime, strftime, sleep
from datetime import datetime, timedelta
import sys
import numpy
import logger
from adjust import *
from depurador import *
from multiprocessing import Process

global builder
global registro
global level
global step
global toggle
global checkLevel
global xe
global xlevel
global contador
global timeOk
global veces
global equipo
global cabezal
global adj

global addr
global baud
global port


registro = "defaultFile"
level = 0
xlevel = 0
step = 0
toggle = 0
checkLevel = 0
contador = 0
timeOk = 0
xe = " hola mundo "
veces = 0
adj = 0

depurador(0, "SADSOr", "**** Arranque del sistema ***")
depurador(0, "SADSOr", "Elegir nivel de detalle de depuración en depurador.py")
depurador(0, "SADSOr", "iNIVEL_TEST0: nada")
depurador(0, "SADSOr", "iNIVEL_TEST3: detallado)")

logger.info(" ****************** Arranque del sistema *******************")

###################################################################################################
# Nombre función: gui_main()
# Entradas: no
# Salidas: no
# Propósito: llama al archivo gui.glade para construir la interfaz gráfica. Ejecuta funciones
#           según qué botones se presionan en la gui y llama a la función main_loop() cada 1
#           seg. para realizar la operación principal de SADSOr.
###################################################################################################
def gui_main():
    global equipo
    global cabezal
    global addr
    global baud
    global port
    global start
    
    path = "/home/cto/SADSOr/"      # Si se requier cambiar el path, también cambiar en los otros scripts.
    
    addr = '/dev/rfcomm0'		                    # Puerto serie Raspberry Pi conectada a BT 
    baud = 115200
        
    builder = Gtk.Builder()
    builder.add_from_file(path+"gui/new_gui.glade")

    equipo = 0
    cabezal = 0
    
    ###################################################################################################
    # Nombre función: rssi()
    # Entradas: no
    # Salidas: level (número proporcional al nivel de señal recibido desde el módulo BT en MS)
    # Propósito: ejecuta el comando rssi y guarda el resultado en el archivo de texto bluetooh.txt.
    #           Luego lee ese archivo y, en caso de conexión, saca el valor númerico del archivo. En
    #           caso de desconexión se produce una excepción por no encontrar el valor numérico y
    #           se le asigna el valor 0 a nivel.
    ###################################################################################################
    
    def rssi():
        global xe
        global xlevel
        global equipo

        barra_de_nivel = builder.get_object("barra_de_nivel")
        etiqueta_nivel = builder.get_object("etiqueta_nivel")

        ruta = str(path+"bluetoothlog.txt")
        
        if equipo == 50:
            os.system(f'hcitool rssi 98:D3:31:FB:16:CE > {ruta}') # MAGNATECH-MS50 514D
        if equipo == 47:
            os.system(f'hcitool rssi 98:D3:31:FC:18:E5 > {ruta}') # MAGNATECH-MS47 514D
        if equipo == 49:
            os.system(f'hcitool rssi 98:D3:31:FB:47:BE > {ruta}') # MAGNATECH-MS49 514D
        if equipo == 32:
            os.system(f'hcitool rssi 98:D3:32:20:A1:61 > {ruta}') # MAGNATECH-MS32 511
        if equipo == 99:
            os.system(f'hcitool rssi 98:D3:32:10:B5:4F > {ruta}') # SEOE INTERNAL MODULE TEST 511
       
        file_name = ruta
        
        # Inicialización de la variable
        level = None 
        try:
            with open(file_name, 'r') as txtfile:
                for line in txtfile:
                    if "RSSI return value:" in line:
                        # Extraemos el valor despues de "RSSI return value:"
                        parts = line.split(":")
                        if len(parts) > 1:
                            level = int(parts[1].strip()) #Convertimos el valor a entero.
                        #Imprimir el resultado
                        if level is not None:
                            level = int(level) + 30
                            depurador(1, "RSSI", f"Conectado con nivel de señal RSSI: {level}")            
                        if abs(level - xlevel) > 4:      # log solo si hubo cambio de nivel de senal en mas de 4 puntos
                            logger.info(" Nivel de señal BT: %s :-)"%level)
                            xlevel = level
                            xe = "Conectado"  # para que ante una desconexión lo indique en el log
                            
                        barra_de_nivel.set_value(level)
                        etiqueta_nivel.set_text("Nivel de Señal:  \n   "+str(level))
                            
                        return level
                        
                depurador(1, "RSSI", "Módulo interno apagado o fuera de alcance")
                if xe == "Conectado":
                    logger.warning(" Desconectado :-(")
                xe = "Desconectado"
                level = 0
                xlevel = 0  # para que ante una re-conexión imprima el nivel de señal
                barra_de_nivel.set_value(level)
                etiqueta_nivel.set_text("Desconectado...")
                return level
        

        except Exception as e:
            depurador(1, "RSSI", f"error: {e}")
            if str(e) != str(xe):
                logger.warning(" Desconectado :-(")
                xe = e
            level = 0
            xlevel = 0  # para que ante una re-conexión imprima el nivel de señal
            barra_de_nivel.set_value(level)
            etiqueta_nivel.set_text("Desconectado...")
            return level
                
    def evento_graficar(button):
        global registro
        global equipo
        global adj
        
        if adj == 0:
            graficar(registro,"No",equipo)
        elif adj == 1:
            graphForAdjust(registro,"No",equipo)

    ###################################################################################################
    # Nombre función: seleccionarRegistro()
    # Entradas: no
    # Salidas: no
    # Propósito: Se ejectua cuando se presiona el botón para buscar un archivo histórico en la gui. Una
    #           vez selecionado el archivo, se lo guarda en la variable global "registro", la cual es
    #           entrada de la funcion graficar(). 
    ###################################################################################################
    def seleccionarRegistro(file_chooser_button):
        global registro
        global equipo
        registro = Gtk.FileChooser.get_filename(file_chooser_button)
        trash, trash, trash, trash, trash, registro = registro.split('/')
        logger.info(" Registro histórico seleccionado: %s"%registro)

    def apagar(button):
        logger.info(" *******************  Apagando sistema  ********************")
        Gtk.main_quit()
        os.system('sudo shutdown -h now')

    def reiniciar(button):
        logger.info(" ******************  Reiniciando sistema  ******************")
        Gtk.main_quit()
        os.system('sudo reboot')

    def conectar():
        global equipo
        
        if equipo == 50:
            os.system('sudo rfcomm connect /dev/rfcomm0 98:D3:31:FB:16:CE 1') # MAGNATECH-MS50

        if equipo == 47:
            os.system('sudo rfcomm connect /dev/rfcomm0 98:D3:31:FC:18:E5 1') # MAGNATECH-MS47

        if equipo == 49:
            os.system('sudo rfcomm connect /dev/rfcomm0 98:D3:31:FB:47:BE 1') # MAGNATECH-MS49

        if equipo == 32:
            os.system('sudo rfcomm connect /dev/rfcomm0 98:D3:32:20:A1:61 1') # MAGNATECH-MS32

        if equipo == 99:
            os.system('sudo rfcomm connect /dev/rfcomm0 98:D3:32:10:B5:4F 1') # MODULO DE TEST SEOE
                

    def controlProceso(script):
        global equipo
                
        #crear y arrancar el proceso.
        p = Process(target=script)
        p.start()
        proceso = p.pid
        
        depurador(1, "PROCESO", f"Se inicia proceso: {script}")
        depurador(3, "PROCESO", f"pid nro: {proceso}")
        
        #return True

    def modoAjuste(button):
        global adj
        etiqueta_ajuste = builder.get_object("etiqueta_ajuste")
        if button.get_active():
            etiqueta_ajuste.set_text("Activado")
            logger.info(" Se activa funcion de ajuste del SADSOr")
            adj = 1
        else:
            etiqueta_ajuste.set_text("Desactivado")  
            logger.info(" Se desactiva funcion de ajuste del SADSOr")
            adj = 0
        return adj

    def eventoSeleccionMS(menuitem):
        global equipo
        global cabezal
        
        opcion_ms = menuitem.get_label()
        etiqueta_ms = builder.get_object("etiqueta_ms")

        if opcion_ms == "SEOE-MS32": 
            equipo = 32
            etiqueta_ms.set_text("SESE-MS32")  
        if opcion_ms == "SESA-MS47": 
            equipo = 47
            etiqueta_ms.set_text("SESA-MS47")  
        if opcion_ms == "SESE-MS49": 
            equipo = 49
            etiqueta_ms.set_text("SESE-MS49")  
        if opcion_ms == "SESE-MS50": 
            equipo = 50
            etiqueta_ms.set_text("SESE-MS50")
        if opcion_ms == "SEOE-TEST": 
            equipo = 99
            etiqueta_ms.set_text("SEOE-TEST")
        
        logger.info(f" Equipo seleccionado: {opcion_ms}")
        depurador(1, "SELECCIÓN_MS", f"{opcion_ms}") 
            
        return True

    def eventoSeleccionCabezal(menuitem):
        global equipo
        global cabezal
        
        opcion_cabezal = menuitem.get_label()
        etiqueta_cabezal = builder.get_object("etiqueta_cabezal") 

        if opcion_cabezal == "Serie 805": 
            cabezal = 805
            etiqueta_cabezal.set_text("Cabezal serie 805")  
        if opcion_cabezal == "Serie 810": 
            cabezal = 810
            etiqueta_cabezal.set_text("Cabezal serie 810")  
        if opcion_cabezal == "Serie C10": 
            cabezal = 10
            etiqueta_cabezal.set_text("Cabezal serie C10")  
            
        logger.info(f" Cabezal seleccionado: {opcion_cabezal}")
        depurador(1, "SELECCION_CAB", f"{opcion_cabezal}") 

        return True

    ###################################################################################################
    # Nombre función: main_loop()
    # Entradas: no
    # Salidas: no
    # Propósito: es ejecutada una vez por segundo dentro de la función principal gui_main() y retorna
    #           rápidamente a fin de refrescar la gui (cada vez que encuentra un "return True").
    #           Las funciones que realiza son:
    #           - Actualiza el reloj cada 1 minuto aprox. a través de la variable "contador".
    #           - Controla el nivel de señal, si el nivel de señal devuelto por la función rssi() es 0,
    #               trata de reconectar cada 1 seg. aprox. (a través del script conectarBT.py)
    #               Si no lo logra, SALE siempre y lo indica en la gui. (STEP = 0)
    #           - En caso de conexión, monitorea el puerto serie (donde está conectado el módulo BT de
    #               la RPi) cada 1 seg. para ver si el PIC está mandando tramas. Si no encuentra tramas
    #               se produce una excepción y se ejecuta la función rssi() cada 10 seg. (a través de)
    #               la variable checkLevel) para monitorear el nivel de señal mientras no entren tramas
    #               y SALE (STEP = 1)
    #           - En caso de detectar una trama (STEP = 2), se llama a la función registrarYalmacenar(),
    #               la cual se encarga de almacenar todas las tramas siguientes
    #               en un archivo de texto tipo "datos_aaaammdd_hhmmss.txt". La función
    #               registrarYalmacenar() es BLOQUEANTE por lo que mientras se reciban tramas, la gui
    #               pierde el refresco (esto es útil ya que el operador no puede tocar nada mientras
    #               se está en proceso de registro). Cuando termina el proceso de soldadura, no se
    #               reciben más tramas y se devuelve el refresco a la gui.
    #           - Luego de registrar las tramas (STEP = 4), se llama a la función graficar().
    #               Se grafica el archivo almacenado en la variable global "registro" modificada en
    #               STEP 2.
    #           - Los STEPs 3 y 5 solo sirven para retornar a la gui y refrescar mensajes. STEP 6
    #               hace una pausa de 5 seg. para dar tiempo de mostrar qué archivo nuevo de datos
    #               se generó, antes de volver a estar preparado para un nuevo proceso.
    #           - STEP 12 permite volver a STEP 0 en caso de que se haya perdido la conexión
    #               con la MS.
    #               
    ###################################################################################################
    def main_loop():
        global step
        global level
        global registro
        global toggle
        global checkLevel
        global contador
        global timeOk
        global veces
        global equipo
        global cabezal
        global adj
        global addr
        global baud
        global start
        
        etiqueta_mensajes = builder.get_object("etiqueta_mensajes")
        etiqueta_tiempo = builder.get_object("etiqueta_tiempo")
        etiqueta_fecha = builder.get_object("etiqueta_fecha")
        etiqueta_hora = builder.get_object("etiqueta_hora")
       
        # print "equipo: MS"+str(equipo)+"  cabezal serie:"+str(cabezal)
                
        contador += 1
        if contador == 1: # cada 60" aprox.
            fecha, hora = str(dt.datetime.utcnow()).split(' ')
            ano, mes, dia = fecha.split('-')
            h, m, s = hora.split(':')
            s, trash = s.split('.')
            if timeOk == 0:
                etiqueta_fecha.set_text("--/--/----")
                etiqueta_hora.set_text("--:--")
            elif timeOk == 1:
                etiqueta_fecha.set_text(dia+"/"+mes+"/"+ano)
                etiqueta_hora.set_text(h+":"+m)
                etiqueta_tiempo.set_text(dia+"/"+mes+"/"+ano+"\n"+"    "+h+":"+m)
                
            return True             # Vuelve al main para poder actualizar etiquetas

        if contador == 3:
            contador = 0        # se resetea variable para volver a calcular y mostar fecha, hora

        if equipo == 0:
            etiqueta_mensajes.set_text("Seleccionar MS para comenzar")
            return True
        
        if cabezal == 0:
            etiqueta_mensajes.set_text("Seleccionar tipo de cabezal para comenzar")
            return True
            
        if (equipo == 47  or equipo == 49 or equipo == 50) and cabezal == 10:
            etiqueta_mensajes.set_text("Cabezal incompatible con MS seleccionada")
            return True

        if equipo == 32 and (cabezal == 805 or cabezal == 810):
            etiqueta_mensajes.set_text("Cabezal incompatible con MS seleccionada")
            return True      


        if level == 0:
            if toggle == 0:
                controlProceso(conectar)
                level = rssi()
                toggle = 1
                return True
            else:
                etiqueta_mensajes.set_text("No hay conexión con MS-%s :-("%equipo) # Si no hago toggle no acutaliza el cartel :-s
                toggle = 0
                step = 12   # 12 es un valor especial para cuando se apaga la MS
                return True   

        if step == 12:      # solo se da cuando se reinicia la MS luego de una conexión anterior
            #etiqueta_mensajes.set_text("Listo para comenzar con %s !"%equipo)
            step = 0
            return True



        if step <= 1:
            try:
                port = serial.Serial(addr,baud,timeout = 0.05)
                
            except: # solo se da cuando se apaga la MS luego de una conexión anterior
                controlProceso(conectar)
                level = rssi()
                return True
            
            if checkLevel == 0:
                level = rssi()
            checkLevel += 1
            if checkLevel == 10:
                checkLevel = 0
            if step == 0:
                ###########################################################################
                if timeOk == 0:
                    depurador(1, "MAIN_LOOP", f"Step = {step} - Intentando configurar fecha y hora en el sistema")
                    timeOk = fechaYhora()
                    if timeOk == 0:
                        depurador(1, "MAIN_LOOP", f"Step = {step} - No se pudo configurar fecha y hora")
                        if veces == 0: 
                            logger.error(" No se pudo configurar fecha y hora \r")
                        veces += 1
                    if veces == 3600:
                        veces = 0    
                    depurador(1, "MAIN_LOOP", f"Step = {step} - Fecha y hora configuradas con éxito")
                    etiqueta_mensajes.set_text("Aguardando actualización de Fecha y Hora... \r")
                    return True
                ############################################################################
                    
                logger.info(" Aguardando inicio del proceso de soldadura...")
                etiqueta_mensajes.set_text("Listo para comenzar con MS-%s !"%equipo)
                step = 1
                depurador(1, "MAIN_LOOP", f"Step = {step} - Esperando tramas...")
                return True

        if step == 1:        
            t_byte_literal = port.read(1)
            if t_byte_literal == b'':
                return True
                
            etiqueta_mensajes.set_text("Registrando soldadura, aguarde por favor...")
            step = 2
            return True
        if step == 2:
            depurador(1, "MAIN_LOOP", f"Step = {step} - Registrando soldadura")
            if adj == 0:
                registro = registrarYalmacenar(equipo, cabezal)
            elif adj == 1:
                registro = recordForAdjust(equipo)
            step = 3
            return True
        if step == 3:
            depurador(1, "MAIN_LOOP", f"Step = {step} - Derivando al módulo graficador")
            etiqueta_mensajes.set_text("Graficando...")
            step = 4
            return True
        if step == 4:
            if adj == 0:
                graficar(registro,"Si",equipo)
                depurador(1, "MAIN_LOOP", f"Step = {step} - Gráfico completo")
            elif adj == 1:
                graphForAdjust(registro,"Si",equipo)
                depurador(1, "MAIN_LOOP", f"Step = {step} - Gráfico completo para ajuste del SADSOr")
            step = 5
            return True
        if step == 5:
            depurador(1, "MAIN_LOOP", f"Step = {step} - Proceso completo, datos guardados en: {registro}.txt")
            logger.info(" Fin del proceso.")           
            etiqueta_mensajes.set_text("Fin del proceso, registro generado: " +registro+ ".txt")
            step = 6
            return True
        if step == 6:
            depurador(1, "MAIN_LOOP", f"Step = {step} - Delay para anotar el nro. de registro")
            sleep(5)
            #level = rssi()
            step = 0
            contador = 0
            return True     

    handlers = {
        "terminar_aplicacion": Gtk.main_quit,
        "evento_graficar": evento_graficar,
        "evento_apagar": apagar,
        "evento_reiniciar": reiniciar,
        "evento_seleccion": seleccionarRegistro,
        "evento_ajustes": modoAjuste,
        "evento_seleccion_ms": eventoSeleccionMS,
        "evento_seleccion_cabezal": eventoSeleccionCabezal
    }

    builder.connect_signals(handlers)
    window = builder.get_object("ventana_principal")
    #filechooserbutton = Gtk.FileChooserButton('Seleccionar Carpeta')
    #filechooserbutton.set_current_folder(path+"data")
    t_busqueda_ms = 1000
    GLib.timeout_add(t_busqueda_ms, main_loop)

    window.show_all()

    

if __name__ == "__main__":
    gui_main()
    Gtk.main()
