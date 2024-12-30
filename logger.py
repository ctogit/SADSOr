#!/usr/bin/python
#~ Emiliano A. Baum, 2014/10/15
#~ Cristian A. Torres 2017/09/14
#~ Modulo de logueo
import logging, logging.handlers
from xml.dom import minidom
from xml.parsers import expat
from os import path,makedirs
#~ Configurando el modulo de logging
#~ Validando existe el directorio
if not path.isdir("logs"):
    makedirs("logs")
FORMAT='%(asctime)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
#~ handler = logging.handlers.RotatingFileHandler("%s%s"%(logs,archivo_log), maxBytes=10000000, backupCount=10)
handler = logging.handlers.RotatingFileHandler("logs/log.txt", maxBytes=10000000, backupCount=10)
handler.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(handler)

def info(data):
    print(data + "\r\n")
    try:
        logger.info(data)
    except:
        pass
    return True

def warning(data):
    print(data)
    try:
        logger.warning(data)
    except:
        pass
    return True

def debug(data):
    print(data)
    logger.debug(data)
    return True

def error(data):
    print(data)
    try:
        logger.error(data)
    except:
        pass
    return True
    
def critical(data):
    print(data)
    try:
        logger.critical(data)
    except:
        pass
    return True
    
