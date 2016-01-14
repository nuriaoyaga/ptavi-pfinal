#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor PROXY
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import XMLHandler
from uaserver import Log
import sys
import socket
import os
import hashlib


# Comprobamos que se introducen datos correctos
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
#Mandamos información en función del método
if METOD == 'REGISTER':
    try:
        OPTION = int(OPTION)
    except ValueError:
        sys.exit("Usage: int OPTION Required")
    if OPTION > 0:
        Log().Log(UA['log_path'], 'init/end', ' ', 'Starting...')
    USER = UA['account_username'] + ":" + UA['uaserver_puerto']
    EXPIRES = "Expires:" + str(OPTION) + '\r\n'
    LINE = METOD + " sip:" + USER + " SIP/2.0\r\n" + EXPIRES
    print ("Enviado:\r\n" + LINE)
    my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
    Log().Log(UA['log_path'], 'send', PROXY, LINE)
elif METOD == 'INVITE':
    print ("Enviando:\r\n" + METOD + " sip:" + OPTION + " SIP/2.0")
    HEAD = METOD + " sip:" + OPTION + " SIP/2.0\r\n"
    HEAD += "Content-Type: application/sdp\r\n\r\n"
    O = "o=" + UA['account_username'] + " " + UA['uaserver_ip'] + " \r\n"
    M = "m=audio " + UA['rtpaudio_puerto'] + " RTP\r\n"
    BODY = "v=0\r\n" + O + "s=BigBang\r\n" + "t=0\r\n" + M
    LINE = HEAD + BODY
    print ("Enviado:\r\n" + LINE)
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
    Log().Log(UA['log_path'], 'receive', PROXY, datadec)
except socket.error:
    SOCKET_ERROR = UA['regproxy_ip'] + " PORT:" + UA['regproxy_puerto']
    Log().Log(UA['log_path'], 'error', ' ', SOCKET_ERROR)
    sys.exit("Error: No server listening at " + PROXY)
proxy = '\r\nVia: SIP/2.0/UDP branch=z87ur749ru8e74\r\n\r\n'
rec = datadec.split(proxy)[0:-1]
#Interpretación de lo recibido
r_401 = "SIP/2.0 401 Unauthorized"
#Autorization
if datadec.split('\r\n')[0] == r_401:
    #Codifica mensaje
    m = hashlib.md5()
    Nonce = datadec.split('=')[1].split('\r\n')[0]
    m.update(bytes(UA['account_passwd'] + Nonce, 'utf-8'))
    RESPONSE = m.hexdigest()
    Line_Authorization = "\r\n" + "Authorization: response="
    Line_Authorization += RESPONSE + "\r\n"
    LINE_REGIST = LINE + Line_Authorization
    print ("Enviado:\r\n" + LINE_REGIST)
    #Envía nueva línea
    my_socket.send(bytes(LINE_REGIST, 'utf-8') + b'\r\n')
    Log().Log(UA['log_path'], 'send', PROXY, LINE_REGIST)
    try:
        data = my_socket.recv(1024)
        datadec = data.decode('utf-8')
        Log().Log(UA['log_path'], 'receive', PROXY, datadec)
        if OPTION == 0:
            Log().Log(UA['log_path'], 'init/end', ' ', 'Finishing...')
    except socket.error:
        SOCKET_ERROR = UA['regproxy_ip'] + " PORT:" + UA['regproxy_puerto']
        Log().Log(UA['log_path'], 'error', ' ', SOCKET_ERROR)
        sys.exit("Error: No server listening at " + PROXY)
#Envío de ACK
elif rec[0:3] == ['SIP/2.0 100 Trying', 'SIP/2.0 180 Ring', 'SIP/2.0 200 OK']:
    LINE_ACK = "ACK sip:" + OPTION + " SIP/2.0\r\n\r\n"
    print("Enviando: " + LINE_ACK)
    my_socket.send(bytes(LINE_ACK, 'utf-8') + b'\r\n')
    rcv_Ip = datadec.split("o=")[1].split(" ")[1].split("s")[0]
    rcv_Port = datadec.split("m=")[1].split(" ")[1]
    aEjecutar = './mp32rtp -i ' + rcv_Ip + ' -p '
    aEjecutar += rcv_Port + " < " + UA['audio_path']
    aEjecutar_cvlc = 'cvlc rtp://@' + rcv_Ip + ':'
    aEjecutar_cvlc += rcv_Port + " 2> /dev/null"
    print ("Vamos a ejecutar", aEjecutar)
    print ("Vamos a ejecutar", aEjecutar_cvlc)
    os.system(aEjecutar)
    os.system(aEjecutar_cvlc + "&")
    print("Ha terminado la ejecución de fichero de audio")
    Log().Log(UA['log_path'], 'send', PROXY, LINE_ACK)
elif datadec == "Acceso denegado: password is incorrect\r\n\r\n":
    print("Usage: The Password is incorrect")
else:
    sys.exit(datadec)
# Cerramos todo
my_socket.close()
