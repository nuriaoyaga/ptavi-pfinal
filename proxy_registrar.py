#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor SIP
en UDP simple
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import Log
import SocketServer
import socket
import sys
import time


class XMLHandler(ContentHandler):

    def __init__(self):
        """
        Constructor. Inicializamos las variables
        """
        self.XML = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['logpath']
        }

        self.config = {}

    def startElement(self, name, attrs):
        """
        Método que se llama cuando se abre una etiqueta
        """
        if name in self.XML:
            for attr in self.XML[name]:
                self.config[name + "_" + attr] = attrs.get(attr, "")
                if name + "_" + attr == 'server_ip':
                    if self.config['server_ip'] == "":
                        self.config['server_ip'] = '127.0.0.1'

    def get_tags(self):
        return self.config


class ProxyRegister(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    users_dic = {}
    METODOS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
    def handle(self):
        caract_dic = {}
        UAC = self.client_address[0] + ' ' + str(self.client_address[1])
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if not line:
                break
            Log().Log(PR['log_logpath'], 'receive', UAC, line)
            respuesta = line.decode('utf-8').split(' ')
            metod = respuesta[0]
            if not metod in self.METODOS:
                LINE = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(resp)
                Log().Log(UA['log_path'], 'receive', FROM, LINE)
            if metod == 'REGISTER':
                #Comprobamos usuarios antiguos y sus tiempos de expiración
                self.json2registered()
                now = time.gmtime(time.time())
                timenow = time.strftime('%Y-%m-%d %H:%M:%S', now)
                Expires_list = []
                for user in self.users_dic:
                    atributes = self.users_dic[user]
                    timeexpiration = atributes["expires"]
                    if timenow > timeexpiration:
                        Expires_list.append(user)
                for expired in Expires_list:
                    del self.users_dic[expired]
                #Asignamos valores recibidos
                usuario = respuesta[1].split(':')[1]
                expires = int(respuesta[2].split(':')[1])
                caract_dic["address"] = self.client_address[0]
                expiration = time.gmtime(int(time.time()) + expires)
                timeexp = time.strftime('%Y-%m-%d %H:%M:%S', expiration)
                caract_dic["expires"] = timeexp
                self.users_dic[usuario] = caract_dic
                #Da de baja al usuario
                if expires == 0:
                    del self.users_dic[usuario]
                LINE = 'SIP/2.0 200 OK\r\n\r\n'
                self.wfile.write(LINE)
                Log().Log(PR['log_logpath'], 'send', UAC, LINE)

            elif :
                self.wfile.write(b"Hemos recibido tu peticion")
                print("El cliente nos manda " + line.decode('utf-8'))


    def register2json(self):
        """
        Método que crea un documento json con los usuarios registrados
        """
        with open('registered.json', 'w') as fichero_json:
            json.dump(self.users_dic, fichero_json, sort_keys=True, indent=4,
                      separators=(',', ':'))

    def json2registered(self):
        """
        Método que crea un diccionario con los usuarios registrados
        anteriormente
        """
        try:
            fich_json = open('registered.json', 'r')
            self.users_dic = json.load(fich_json)
        except:
            self.users_dic = {}


if __name__ == "__main__":
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        sys.exit("Invalid Port")
    # Creamos servidor de eco y escuchamos
    serv = socketserver.UDPServer(('', PORT), SIPRegisterHandler)
    print("Lanzando servidor UDP de eco...")
    serv.serve_forever()
