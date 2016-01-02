#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de SIP con INVITE, ACK y BYE
"""

import socketserver
import sys
import os

if len(sys.argv) != 4:
    sys.exit('Usage: python server.py IP port audio_file')

try:
    IP_SERV = sys.argv[1]
    PORT_SERV = int(sys.argv[2])
    FICHERO = sys.argv[3]
except Exception:
    sys.exit('Usage: python server.py IP port audio_file')
if not os.path.exists(FICHERO):
    sys.exit('Usage: python server.py IP port audio_file')


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Servidor SIP con INVITE, ACK y BYE
    """
    METODOS = ['INVITE', 'BYE', 'ACK']

    def handle(self):
        global Puerto_RTP
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            metod = line.decode('utf-8').split(' ')[0]
            if not metod in self.METODOS:
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')
            elif metod == 'INVITE':
                Puerto_RTP = ""
                send = b'SIP/2.0 100 Trying\r\n\r\n'
                send += b'SIP/2.0 180 Ring\r\n\r\n'
                send += b'SIP/2.0 200 OK\r\n\r\n'
                send += "Content-Type: application/sdp \r\n\r\n" + "v=0 \r\n" +
                         + "o=" + USUARIO + " " + IP + ' \r\n' + "s=BigBang"
                         + ' \r\n' + "t=0" + ' \r\n' + "m=audio "
                         + str(PUERTO_AUDIO) + ' RTP' + '\r\n\r\n'
                self.wfile.write(send)
            elif metod == 'ACK':
                aEjecutar = './mp32rtp -i' + IP + '-p' + + str(Puerto_RTP) +
                            + ' < ' + PATH_AUDIO
                print ('Vamos a ejecutar', aEjecutar)
                os.system(aEjecutar)
            elif metod == 'BYE':
                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
            else:
                self.wfile.write(b'SIP/2.0 400 Bad request\r\n\r\n')


if __name__ == "__main__":
    #Lanzando un servidor SIP
    Puerto_RTP = []
    print('Listening...')
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
    #Conexion con el proxy
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((IP_PROXY, PUERTO_PROXY))

    serv = socketserver.UDPServer((IP, int(PUERTO)), EchoHandler)
    serv.serve_forever()
