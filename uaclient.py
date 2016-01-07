#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor SIP
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import XMLHandler
from uaserver import Log
import sys
import socket
import os
import time

# Cliente UDP simple.
if len(sys.argv) != 4:
    sys.exit('Usage: python uaclient.py config method option')
try:
    CONFIG = sys.argv[1]
    METOD = sys.argv[2].upper()
    OPTION = sys.argv[3]
except Exception:
    sys.exit('Usage: python uaclient.py config method option')
#lectura de fichero xml
parser = make_parser()
cHandler = XMLHandler()
parser.setContentHandler(cHandler)
parser.parse(open(CONFIG))
UA = cHandler.get_tags()
# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((UA['regproxy_ip'], int(UA['regproxy_puerto'])))
PROXY = UA['regproxy_ip'] + ':' + UA['regproxy_puerto']
if METOD == 'REGISTER':
    try:
        OPTION = int(OPTION)
    except ValueError:
        sys.exit("Usage: int OPTION Required")
    USER = UA['account_username'] + ":" + UA['uaserver_puerto']
    EXPIRES = "Expires:" + str(OPTION) + '\r\n'
    LINE = METOD + " sip:" + USER + " SIP/2.0\r\n" + EXPIRES
    print ("Enviado:\r\n" + LINE)
    my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
    Log().Log(UA['log_path'],'init/end', ' ', 'Starting...')
    Log().Log(UA['log_path'], 'send', PROXY, LINE)
elif METOD == 'INVITE':
    print ("Enviando:\r\n" + METOD + " sip:" + OPTION + " SIP/2.0")
    HEAD = METOD + " sip:" + OPTION + " SIP/2.0\r\n"
    HEAD += "Content-Type: application/sdp\r\n\r\n"
    O = "o=" + UA['account_username'] + " " + UA['uaserver_ip'] + " \r\n"
    M = "m=audio " + UA['rtpaudio_puerto'] + " RTP\r\n"
    BODY = "v=0\r\n" + O + "s=BigBang\r\n" + "t=0\r\n" + M
    LINE = HEAD + BODY
    my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
    Log().Log(UA['log_path'], 'send', PROXY, LINE)
elif METOD == 'BYE':
    LINE = METOD + " sip:" + OPTION + " SIP/2.0\r\n"
    print ("Enviando:\r\n" + LINE)
    my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
    Log().Log(UA['log_path'], 'send', PROXY, LINE)
#Decodificación de lo recibido
try:
    data = my_socket.recv(1024)
    datadec = data.decode('utf-8')
    rec = datadec.split('\r\n\r\n')[0:-1]
    print (rec)
except socket.error:
    SOCKET_ERROR = UA['regproxy_ip'] + " PORT:" + UA['regproxy_puerto']
    Log().Log(UA['log_path'], 'error',' ', SOCKET_ERROR)
    sys.exit("Error: No server listening at " + SOCKET_ERROR)
#Interpretación de lo recibido
Log().Log(UA['log_path'], 'receive:', PROXY, datadec)
r_400 = "SIP/2.0 400 Bad Request\r\n\r\n"
r_404 = "SIP/2.0 404 User Not Found\r\n\r\n"
r_405 = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
r_401 = "SIP/2.0 401 Unauthorized\r\n"
if datadec == r_400 or datadec == r_404 or datadec == r_405 :
    sys.exit(detadec)
    #m = hashlib.md5()
    #Nonce = rec[1].split('=')[1]
    #m.update(bytes(UA['account_passwd'] + Nonce, 'utf-8'))
    #RESPONSE = m.hexdigest()
    #Line_Authorization = "Authorization: response=" + RESPONSE + "\r\n"
    #LINE_REGIST = LINE + Line_Authorization
    #my_socket.send(bytes(LINE_REGIST, 'utf-8') + b'\r\n')
else:
    if METOD == "INVITE":
        LINE_ACK = "ACK sip:" + OPTION + " SIP/2.0\r\n\r\n"
        print("Enviando: " + LINE_ACK)
        my_socket.send(bytes(LINE_ACK, 'utf-8') + b'\r\n')
        print(datadec)
        rcv_Ip = datadec.split("o=")[1].split(" ")[1].split("s")[0]
        rcv_Port = datadec.split("m=")[1].split(" ")[1]
        aEjecutar = './mp32rtp -i ' + rcv_Ip + ' -p '
        aEjecutar += rcv_Port + " < " + UA['audio_path']
        print ("Vamos a ejecutar", aEjecutar)
        os.system(aEjecutar)
        print("Ha terminado la ejecución de fichero de audio")
        Log().Log(UA['log_path'], 'send', PROXY, LINE_ACK)
    elif METOD == "REGISTER":
        pass
    elif METOD == "BYE":
        Log().Log(UA['log_path'], 'init/end', ' ', 'Finishing...\n')
    else:
        sys.exit(detadec)
# Cerramos todo
my_socket.close()
