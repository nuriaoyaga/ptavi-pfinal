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
import json


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
                self.UAS = self.users_dic[usuario]

    """
    Echo server class
    """
    users_dic = {}
    UAS = {}
    METODOS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
    def handle(self):
        UAC = self.client_address[0] + ' ' + str(self.client_address[1])
        caract_dic = {}
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if not line:
                break
            Log().Log(PR['log_path'], 'receive', UAC, line.decode('utf-8'))
            respuesta = line.decode('utf-8').split(' ')
            print(respuesta)
            metod = respuesta[0]
            if not metod in self.METODOS:
                LINE = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(bytes(LINE, 'utf-8'))
                Log().Log(UA['log_path'], 'receive', FROM, LINE)
            if metod == 'REGISTER':
                #Comprobamos usuarios antiguos y sus tiempos de expiración
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
                caract_dic["port"] = int(respuesta[1].split(':')[2])
                expiration = time.gmtime(int(time.time()) + expires)
                timeexp = time.strftime('%Y-%m-%d %H:%M:%S', expiration)
                caract_dic["expires"] = timeexp
                self.users_dic[usuario] = caract_dic
                #Da de baja al usuario
                if expires == 0:
                    del self.users_dic[usuario]
                self.register2json()
                LINE = 'SIP/2.0 200 OK\r\n\r\n'
                self.wfile.write(bytes(LINE, 'utf-8'))
                Log().Log(PR['log_path'], 'send', UAC, LINE)
            elif metod == 'INVITE':
                usuario = respuesta[1].split(':')[1]
                print(usuario)
                self.Buscar_usuario(usuario)
                if self.UAS == {}:
                    LINE = "SIP/2.0 404 User Not Found\r\n\r\n"
                    self.wfile.write(bytes(LINE, 'utf-8'))
                    Log().Log(PR['log_path'], 'send', UAC, LINE)
                else:
                    my_sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    my_sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_sck.connect((self.UAS["address"], self.UAS["port"]))
                    my_sck.send(line)
                    UASAD = self.UAS["address"] + '' + str(self.UAS["port"])
                    Log().Log(PR['log_path'], 'send', UASAD, line.decode('utf-8'))
                    try:
                        data = my_sck.recv(1024)
                        datadec = data.decode('utf-8')
                    except socket.error:
                        SCK_ERROR =  self.UAS["address"] + " PORT:" + str(self.UAS["port"])
                        Log().Log(PR['log_path'], 'error',' ', SCK_ERROR)
                        sys.exit("Error: No server listening at " + SCK_ERROR)
                    self.wfile.write(bytes(datadec, 'utf-8'))
                    Log().Log(PR['log_path'], 'receive', UASAD, datadec)
                    Log().Log(PR['log_path'], 'send', UAC, datadec)
            elif metod == 'ACK':
                usuario = respuesta[1].split(':')[1]
                self.Buscar_usuario(usuario)
                my_sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_sck.connect((self.UAS["address"], self.UAS["port"]))
                my_sck.send(line)
                UASAD = self.UAS["address"] + '' + str(self.UAS["port"])
                Log().Log(PR['log_path'], 'send', UASAD, line.decode('utf-8'))
            elif metod == 'BYE':
                usuario = respuesta[1].split(':')[1]
                print(usuario)
                self.Buscar_usuario(usuario)
                if self.UAS == {}:
                    LINE = "SIP/2.0 404 User Not Found\r\n\r\n"
                    self.wfile.write(bytes(LINE, 'utf-8'))
                    Log().Log(PR['log_path'], 'send', UAC, LINE)
                else:
                    UASAD = self.UAS["address"] + '' + str(self.UAS["port"])
                    my_sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    my_sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_sck.connect((self.UAS["address"], self.UAS["port"]))
                    my_sck.send(line)
                    try:
                        data = my_sck.recv(1024)
                        datadec = data.decode('utf-8')
                    except socket.error:
                        SCK_ERROR =  self.UAS["address"] + " PORT:" + str(self.UAS["port"])
                        Log().Log(PR['log_path'], 'error',' ', SCK_ERROR)
                        sys.exit("Error: No server listening at " + SCK_ERROR)
                    self.wfile.write(bytes(datadec, 'utf-8'))
                    Log().Log(PR['log_path'], 'receive', UASAD, datadec)
                    Log().Log(PR['log_path'], 'send', UAC, datadec)
            else:
                UASAD = self.UAS["address"] + '' + str(self.UAS["port"])
                LINE = "SIP/2.0 400 Bad Request\r\n\r\n"
                self.wfile.write(bytes(LINE, 'utf-8'))
                Log().Log(PR['log_logpath'], 'send', UASAD, LINE)


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
