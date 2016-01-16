#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de SIP con INVITE, ACK y BYE
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import socketserver
import sys
import os
import time
import threading


class Thread_CVLC(threading.Thread):
    """
    Thread class
    """

    def __init__(self, Port, Ip, Path):
        threading.Thread.__init__(self)
        self.Port = Port
        self.Ip = Ip
        self.Path = Path

    def run(self):
        try:
            aEjecutarcvlc = 'cvlc rtp://@' + self.Ip + ':'
            aEjecutarcvlc += str(self.Port) + ' &'
            os.system(aEjecutarcvlc)
            aEjecutar = './mp32rtp -i ' + self.Ip + ' -p '
            aEjecutar += str(self.Port) + '<' + self.Path
            os.system(aEjecutar)
            print("Ha terminado la ejecución del archivo de audio")
        except:
            sys.exit("Usage: Error en ejecución")


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
        """
        Método que crea un fichero de log y lo actualiza
        """
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


class ServerHandler(socketserver.DatagramRequestHandler):
    """
    Servidor SIP con INVITE, ACK y BYE
    """
    METODOS = ['INVITE', 'BYE', 'ACK']
    rcv_Ip = ""
    rcv_Port = ""

    def handle(self):
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            # Si no hay más líneas salimos del bucle infinito
            if not line:
                break
            linedec = line.decode('utf-8')
            FROM = self.client_address[0] + ' ' + str(self.client_address[1])
            Log().Log(UA['log_path'], 'receive', FROM, linedec)
            metod = linedec.split(' ')[0]
            if not metod in self.METODOS:
                LINE = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(LINE)
                print("Enviamos" + LINE)
                Log().Log(UA['log_path'], 'receive', FROM, LINE)
            else:
                if metod == 'INVITE':
                    #Variables necesarias para el envio de rtp
                    origen = linedec.split("o=")[1]
                    self.rcv_Ip = origen.split(" ")[1].split("s")[0]
                    self.rcv_Port = linedec.split("m=")[1].split(" ")[1]
                    #Respuesta al invite
                    LINE = "SIP/2.0 100 Trying\r\n\r\n"
                    LINE += "SIP/2.0 180 Ring\r\n\r\n"
                    LINE += "SIP/2.0 200 OK\r\n\r\n"
                    HEAD = "Content-Type: application/sdp\r\n\r\n"
                    O = "o=" + UA['account_username'] + " " + UA['uaserver_ip']
                    O += " \r\n"
                    M = "m=audio " + UA['rtpaudio_puerto'] + " RTP\r\n"
                    BODY = "v=0\r\n" + O + "s=BigBang\r\n" + "t=0\r\n" + M
                    LINE += HEAD + BODY
                    self.wfile.write(bytes(LINE, 'utf-8'))
                    print("Enviamos" + LINE)
                    Log().Log(UA['log_path'], 'send', FROM, LINE)
                elif metod == 'ACK':
                    ejecutar = Thread_CVLC(self.rcv_Port, self.rcv_Ip,
                                           UA['audio_path'])
                    ejecutar.start()
                    ejecutar.join()
                elif metod == 'BYE':
                    LINE = "SIP/2.0 200 OK\r\n\r\n"
                    self.wfile.write(bytes(LINE, 'utf-8'))
                    print("Enviamos" + LINE)
                    Log().Log(UA['log_path'], 'receive', FROM, LINE)
                else:
                    LINE = "SIP/2.0 400 Bad Request\r\n\r\n"
                    self.wfile.write(bytes(LINE, 'utf-8'))
                    print("Enviamos" + LINE)
                    Log().Log(UA['log_path'], 'receive', FROM, LINE)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('Usage: python uaclient.py config method option')
    #Apertura del fichero de configuración
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python server.py config")
    #Lectura del XML
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    UA = cHandler.get_tags()
    port = int(UA['uaserver_puerto'])
    serv = socketserver.UDPServer(("", port), ServerHandler)
    print ("Listening...")
    Log().Log(UA['log_path'], 'Init/end', ' ', 'Starting...')
    serv.serve_forever()
