#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor SIP
en UDP simple
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import Log
import socketserver
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
            'log': ['path']
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

    def Buscar_usuario(self, usuario):
        for Client in self.users_dic:
            if usuario == Client:
                self.caract_dic = self.users_dic[usuario]

    """
    Echo server class
    """
    users_dic = {}
    caract_dic = {}
    METODOS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
    def handle(self):
        UAC = self.client_address[0] + ' ' + str(self.client_address[1])
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            print (line)
            if not line:
                break
            Log().Log(PR['log_path'], 'receive', UAC, line.decode('utf-8'))
            respuesta = line.decode('utf-8').split(' ')
            print(respuesta)
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
                self.caract_dic["address"] = self.client_address[0]
                expiration = time.gmtime(int(time.time()) + expires)
                timeexp = time.strftime('%Y-%m-%d %H:%M:%S', expiration)
                self.caract_dic["expires"] = timeexp
                self.users_dic[usuario] = self.caract_dic
                #Da de baja al usuario
                if expires == 0:
                    del self.users_dic[usuario]
                LINE = 'SIP/2.0 200 OK\r\n\r\n'
                self.wfile.write(LINE)
                Log().Log(PR['log_path'], 'send', UAC, LINE)
            else:
                pass
            #elif metod == 'INVITE':
                #usuario = respuesta[1].split(':')[1]
                #Buscar_usuario(usuario)
                #if UAS = {}:
                    #LINE = "SIP/2.0 404 User Not Found\r\n\r\n"
                    #self.wfile.write(LINE)
                    #Log().Log(PR['log_logpath'], 'send', UAC, LINE)
                #self.wfile.write(b"Hemos recibido tu peticion")
                #print("El cliente nos manda " + line.decode('utf-8'))


    def register2json(self):
        """
        Método que crea un documento json con los usuarios registrados
        """
        with open(PR['database_path'], 'w') as fichero_json:
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
    if len(sys.argv) != 2:
        sys.exit('Usage: python uaclient.py config method option')
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python proxy_registrar.py config")
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    PR = cHandler.get_tags()
    # Creamos servidor de eco y escuchamos
    serv = socketserver.UDPServer(("", int(PR['server_puerto'])), ProxyRegister)
    # Escribimos inicio log_proxy.txt
    Log().Log(PR['log_path'], 'Init/end', ' ', 'Starting...')
    print("Lanzando servidor UDP de eco...")
    serv.serve_forever()
