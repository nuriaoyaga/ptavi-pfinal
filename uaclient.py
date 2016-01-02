#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Programa cliente que abre un socket a un servidor SIP
"""

import socket
import sys

# Cliente UDP simple.
if len(sys.argv) != 3:
    sys.exit('Usage: python client.py method receiver@IP:SIPport')
try:
    METOD = sys.argv[1].upper()
    RECEPTOR = sys.argv[2].split('@')[0]
    IP_REC = sys.argv[2].split('@')[1].split(':')[0]
    PORT_REC = int(sys.argv[2].split('@')[1].split(':')[1])
except Exception:
    sys.exit('Usage: python client.py method receiver@IP:SIPport')

# Contenido que vamos a enviar
LINE = METOD + ' sip:' + RECEPTOR + '@' + IP_REC + ' SIP/2.0\r\n'

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((IP_REC, PORT_REC))

print("Enviando: " + LINE)
my_socket.send(bytes(LINE, 'utf-8') + b'\r\n')
data = my_socket.recv(1024)

#Envio del ACK si se recibe el TRYING,RING y OK
rec_invite = data.decode('utf-8').split('\r\n\r\n')[0:-1]
if rec_invite == ['SIP/2.0 100 Trying', 'SIP/2.0 180 Ring', 'SIP/2.0 200 OK']:
    LINE_ACK = 'ACK sip:' + RECEPTOR + '@' + IP_REC + ' SIP/2.0\r\n'
    print("Enviando: " + LINE_ACK)
    my_socket.send(bytes(LINE_ACK, 'utf-8') + b'\r\n')
    data = my_socket.recv(1024)

# Cerramos todo
my_socket.close()
