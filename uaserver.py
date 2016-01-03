#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de SIP con INVITE, ACK y BYE
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import SocketServer
import sys
import os
import time


class XMLHandler(ContentHandler):

    def __init__(self):
        """
        Constructor. Inicializamos las variables
        """
        self.XML = {
            'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']
        }
        self.config = {}

    def startElement(self, name, attrs):
        """
        Método que se llama cuando se abre una etiqueta
        """
        if name in self.XML:
            for attr in self.XML[name]:
                self.config[name + "_" + attr] = attrs.get(attr, "")
                if name + "_" + attr == 'uaserver_ip':
                    if self.config['uaserver_ip'] == "":
                        self.config['uaserver_ip'] = '127.0.0.1'

    def get_tags(self):
        return self.config


class Log(ContentHandler):
    def Log(self, fichero, tipo, to, message):
        fich = open(fichero, 'a')
        Time = time.strftime('%Y%m%d%H%M%S', time.gmtime())
        message = message.replace('\r\n', ' ') + '\n'
        if tipo == 'send':
            fich.write(Time + ' Sent to ' + to + ': ' + message)
        elif tipo == 'receive':
            fich.write(Time + ' Received from ' + to + ': ' + message)
        elif tipo == 'error':
            fich.write(Time + "Error: No server listening at: " + message)
        elif tipo == 'init/end':
            fich.write(Time + ' ' + message)
        fich.close()



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
            Log().Log(UA['log_path'], 'receive', FROM, line)
            metod = line.decode('utf-8').split(' ')[0]
            FROM = self.client_address[0] + ' ' + str(self.client_address[1])
            if not metod in self.METODOS:
                LINE = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(resp)
                Log().Log(UA['log_path'], 'receive', FROM, LINE)
            else:
                if metod == 'INVITE':
                    Log().Log(UA['log_path'], 'receive', FROM, line)
                    LINE = b'SIP/2.0 100 Trying\r\n\r\n'
                    LINE += b'SIP/2.0 180 Ring\r\n\r\n'
                    LINE += b'SIP/2.0 200 OK\r\n\r\n'
                    LINE += "Content-Type: application/sdp \r\n\r\n" +
                             + "v=0 \r\n" + "o=" + USUARIO + " " + IP + ' \r\n'+
                             + "s=BigBang" + ' \r\n' + "t=0" + ' \r\n' +
                             + "m=audio " + str(PUERTO_AUDIO) + ' RTP' +
                             + '\r\n\r\n'
                    self.wfile.write(LINE)
                    Log().Log(UA['log_path'], 'send', FROM, LINE)
                elif metod == 'ACK':
                    rcv_Ip = line.split("o=")[1].split(" ")[1].split("s")[0]
                    rcv_Port = line.split("m=")[1].split(" ")[1]
                    aEjecutar = './mp32rtp -i' + rcv_Ip + '-p' +
                    aEjecutar+= str(rcv_Port) +' < ' + UA['audio_path']
                    print ('Vamos a ejecutar', aEjecutar)
                    os.system(aEjecutar)
                    print("Ha terminado la ejecución de fich de audio")
                elif metod == 'BYE':
                    LINE = "SIP/2.0 200 OK\r\n\r\n"
                    self.wfile.write(LINE)
                    Log().Log(UA['log_path'], 'receive', FROM, LINE)
                else:
                    LINE = "SIP/2.0 400 Bad Request\r\n\r\n"
                    self.wfile.write(LINE)
                    Log().Log(UA['log_path'], 'receive', FROM, LINE)
                    

if __name__ == "__main__":
    #Apertura del fichero de configuración
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python server.py config")
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    UA = cHandler.get_tags()
    serv = SocketServer.UDPServer(("", int(UA['uaserver_puerto'])), ServerHandler)
    print "Listening..."
    Log().Log(UA['log_path'], 'Init/end', ' ', 'Starting...')
    serv.serve_forever()
