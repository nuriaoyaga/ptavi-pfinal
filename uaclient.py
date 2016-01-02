#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor SIP
"""

import socket
import sys

# Cliente UDP simple.
if len(sys.argv) != 4:
    sys.exit('Usage: python uaclient.py config method option')
try:
    CONFIG = sys.argv[1]
    METOD = sys.argv[2].upper()
    OPTION = sys.argv[3]

    #Apertura del fichero de configuración
    fich = open(CONFIG, 'r')
    line = fich.readlines()
    fich.close()

    #USUARIO
    line_account = line[1].split(">")
    account = line_account[0].split("=")[1]
    USUARIO = account.split(" ")[0][1:-1]
    #CONTRASEÑA
    passw = line_account[0].split("=")[2]
    PASSWORD = passw.split(" ")[0][1:-1]
    #IP
    line_uaserver = line[2].split(">")
    uaserver = line_uaserver[0].split("=")[1]
    IP = uaserver.split(" ")[0][1:-1]
    #PUERTO
    uaserver1 = line_uaserver[0].split("=")[2]
    PUERTO = uaserver1.split(" ")[0][1:-1]
    #PUERTO AUDIO RTP
    line_rtp = line[3].split(">")
    rtpaudio = line_rtp[0].split("=")[1]
    PUERTO_AUDIO = rtpaudio.split(" ")[0][1:-1]
    #IP DEL PROXY
    line_regproxy = line[4].split(">")
    regproxy = line_regproxy[0].split("=")[1]
    IP_PROXY = regproxy.split(" ")[0][1:-1]
    #PUERTO DEL PROXY
    regproxy1 = line_regproxy[0].split("=")[2]
    PUERTO_PROXY = regproxy1.split(" ")[0][1:-1]
    #PATH DEL LOG
    line_log = line[5].split(">")
    log = line_log[0].split("=")[1]
    PATH_LOG = log.split(" ")[0][1:-1]
    #PATH DEL AUDIO
    line_audio = line[6].split(">")
    audio = line_audio[0].split("=")[1]
    PATH_AUDIO = audio.split(" ")[0][1:-1]

except Exception:
    sys.exit('Usage: python uaclient.py config method option')

METODOS = ['INVITE', 'BYE', 'REGISTER']
if METOD not in METODOS:
    sys.exit('Usage: python uaclient.py config method option')


# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((IP_REC, PORT_REC))

if METOD == 'REGISTER':
    LINEA1 = "REGISTER " + "sip:" + USUARIO
    LINEA1 += ":" + PUERTO + " SIP/2.0\r\n" + "Expires: " + OPTION + "\r\n\r\n"
    Contrasena = ' Password: ' + PASSWORD + ' \r\n'
    my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
    data = my_socket.recv(1024)
    if OPTION == '0':
        print "Terminando socket..."
        my_socket.close()



#Envio del ACK si se recibe el TRYING,RING y OK
rec_invite = data.decode('utf-8').split('\r\n\r\n')[0:-1]
if rec_invite == ['SIP/2.0 100 Trying', 'SIP/2.0 180 Ring', 'SIP/2.0 200 OK']:
    LINE_ACK = 'ACK sip:' + RECEPTOR + '@' + IP_REC + ' SIP/2.0\r\n'
    print("Enviando: " + LINE_ACK)
    my_socket.send(bytes(LINE_ACK, 'utf-8') + b'\r\n')
    data = my_socket.recv(1024)

# Cerramos todo
my_socket.close()
