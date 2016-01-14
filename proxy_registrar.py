#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor PROXY
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import Log
import socketserver
import socket
import sys
import time
import json
import hashlib
import random


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
    users_dic = {}
    UAS = {}
    METODOS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
    NONCE = random.getrandbits(100)
    Envios = {}

    def Buscar_usuario(self, usuario):
        """
        Método que busca si un usuario está registrado
        """
        for Client in self.users_dic:
            if usuario == Client:
                self.UAS = self.users_dic[usuario]

    def UserRegist(self, usuario):
        register = 'False'
        for Client in self.users_dic:
            if usuario == Client:
                register = 'True'
        return register

    def Conectar_Enviar_Decod(self, ip, puerto, line):
        """
        Método que conecta a un socket, envía y decodifica lo recibido
        """
        #Conexión y envío
        datos = line.decode('utf-8')
        numpuerto = PORTVal(puerto)
        IPVal(ip)
        LINE = datos + 'Via: SIP/2.0/UDP branch=z87ur749ru8e74\r\n'
        my_sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_sck.connect((ip, numpuerto))
        my_sck.send(bytes(LINE, 'utf-8'))
        Ip = self.client_address[0]
        Port = self.client_address[1]
        UAC = Ip + ' ' + str(Port)
        UASAD = ip + ' ' + puerto
        Log().Log(PR['log_path'], 'send', UASAD, LINE)
        print("Enviamos: " + LINE)
        #Recibe, decodifica y responde
        try:
            data = my_sck.recv(1024)
            datadec = data.decode('utf-8')
        except socket.error:
            SCK_ERROR = ip + " PORT:" + puerto
            Log().Log(PR['log_path'], 'error', ' ', SCK_ERROR)
            sys.exit("Error: No server listening at " + SCK_ERROR)
        Log().Log(PR['log_path'], 'receive', UASAD, datadec)
        rec = datadec.split('\r\n\r\n')[0:-1]
        PROXY = 'Via: SIP/2.0/UDP branch=z87ur749ru8e74\r\n\r\n'
        if rec[0:3] == ['SIP/2.0 100 Trying', 'SIP/2.0 180 Ring',
                        'SIP/2.0 200 OK']:
            SDP = datadec.split('SIP/2.0 200 OK\r\n\r\n')[1]
            LINE = rec[0] + "\r\n" + PROXY
            LINE += rec[1] + "\r\n" + PROXY
            LINE += rec[2] + "\r\n" + PROXY
            LINE += SDP
        else:
            LINE = datadec.split("\r\n\r\n")[0]
            LINE += "\r\n" + PROXY
        self.wfile.write(bytes(LINE, 'utf-8'))
        Log().Log(PR['log_path'], 'send', UAC, LINE)

    def CheckPsswd(self, Path, Passwd, User_agent, Ip, Puerto):
        """
        Método que comprueba la contraseña
        """
        Found = 'False'
        #Abrimos el fichero de contraseñas
        fich = open(Path, 'r')
        lines = fich.readlines()
        #Comprobamos línea a línea si exixte el par usuario-contraseña
        for line in range(len(lines)):
            User = lines[line].split(' ')[1]
            Password = lines[line].split(' ')[3]
            Nonce = str(self.NONCE)
            #Para comparar debemos codificar lo que hay en el fichero
            m = hashlib.md5()
            m.update(bytes(Password + Nonce, 'utf-8'))
            RESPONSE = m.hexdigest()
            if User == User_agent:
                if RESPONSE == Passwd:
                    Found = 'True'
        fich.close()
        return Found

    def handle(self):
        """
        Método que maneja el proxy
        """
        caract_dic = {}
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            if not line:
                break
            Ip = self.client_address[0]
            Port = self.client_address[1]
            UAC = Ip + ' ' + str(Port)
            Log().Log(PR['log_path'], 'receive', UAC, line.decode('utf-8'))
            respuesta = line.decode('utf-8').split(' ')
            metod = respuesta[0]
            self.json2registered()
            if not metod in self.METODOS:
                LINE = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(bytes(LINE, 'utf-8'))
                Log().Log(PR['log_path'], 'receive', UAC, LINE)
            if metod == 'REGISTER':
                #Comprobamos autorizacion
                if len(respuesta) == 3:
                    LINE = 'SIP/2.0 401 Unauthorized\r\n'
                    LINE += 'WWW Authenticate: Digest nonce=' + str(self.NONCE)
                    LINE += '\r\n\r\n'
                    self.wfile.write(bytes(LINE, 'utf-8'))
                    print("Enviamos: " + LINE)
                    Log().Log(PR['log_path'], 'send', UAC, LINE)
                else:
                    usuario = respuesta[1].split(':')[1]
                    pwd = respuesta[4].split('=')[1].split('\r\n')[0]
                    Found = self.CheckPsswd(PR['database_passwdpath'], pwd,
                                            usuario, Ip, Port)
                    if Found == 'True':
                        #Comprobamos usuarios antiguos
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
                        expire = respuesta[2].split('\r\n')[1].split(':')[1]
                        expires = int(expire)
                        caract_dic["address"] = self.client_address[0]
                        p = respuesta[1].split(':')[2]
                        caract_dic["port"] = PORTVal(p)
                        expiration = time.gmtime(int(time.time()) + expires)
                        timexp = time.strftime('%Y-%m-%d %H:%M:%S', expiration)
                        caract_dic["expires"] = timexp
                        self.users_dic[usuario] = caract_dic
                        #Da de baja al usuario
                        if expires == 0:
                            del self.users_dic[usuario]
                        self.register2json()
                        LINE = 'SIP/2.0 200 OK\r\n\r\n'
                        self.wfile.write(bytes(LINE, 'utf-8'))
                        print("Enviamos: " + LINE)
                        Log().Log(PR['log_path'], 'send', UAC, LINE)
                    else:
                        LINE = 'Acceso denegado: password is incorrect\r\n\r\n'
                        self.wfile.write(bytes(LINE, 'utf-8'))
                        print("Enviamos: " + LINE)
                        Log().Log(PR['log_path'], 'receive', UAC, LINE)
            elif metod == 'INVITE':
                cliente = respuesta[3].split('=')[2]
                reg = self.UserRegist(cliente)
                if reg == 'False':
                    sys.exit('User must be registered')
                else:
                    usuario = respuesta[1].split(':')[1]
                    self.Buscar_usuario(usuario)
                    if self.UAS == {}:
                        LINE = "SIP/2.0 404 User Not Found\r\n"
                        LINE += 'Via: SIP/2.0/UDP branch=z87ur749ru8e74'
                        LINE += '\r\n\r\n'
                        self.wfile.write(bytes(LINE, 'utf-8'))
                        print("Enviamos: " + LINE)
                        Log().Log(PR['log_path'], 'send', UAC, LINE)
                    else:
                        v = respuesta[3].split('\r\n')[2].split('=')[0]
                        o = respuesta[3].split('\r\n')[3].split('=')[0]
                        s = respuesta[5].split('\r\n')[1].split('=')[0]
                        t = respuesta[5].split('\r\n')[2].split('=')[0]
                        m = respuesta[5].split('\r\n')[3].split('=')[0]
                        if [v, o, s, t, m] == ['v', 'o', 's', 't', 'm']:
                            #Pasa lo que ha recibido al servidor
                            port = str(self.UAS["port"])
                            ip = self.UAS["address"]
                            UASAD = ip + ' ' + port
                            self.Envios[cliente] = usuario
                            self.Envios[usuario] = cliente
                            print(self.Envios)
                            self.Conectar_Enviar_Decod(ip, port, line)
                        else:
                            UASAD = self.UAS["address"]
                            UASAD += '' + str(self.UAS["port"])
                            LINE = "SIP/2.0 400 Bad Request\r\n"
                            LINE += 'Via: SIP/2.0/UDP branch=z87ur749ru8e74'
                            LINE += '\r\n\r\n'
                            self.wfile.write(bytes(LINE, 'utf-8'))
                            print("Enviamos: " + LINE)
                            Log().Log(PR['log_logpath'], 'send', UASAD, LINE)

            elif metod == 'ACK':
                usuario = respuesta[1].split(':')[1]
                self.Buscar_usuario(usuario)
                LINE = line.decode('utf-8').split("\r\n\r\n")[0] + "\r\n"
                LINE += 'Via: SIP/2.0/UDP branch=z87ur749ru8e74\r\n\r\n'
                #Conecta con el servidor y envía ACK
                my_sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_sck.connect((self.UAS["address"], self.UAS["port"]))
                my_sck.send(bytes(LINE, 'utf-8'))
                print("Enviamos: " + LINE)
                UASAD = self.UAS["address"] + '' + str(self.UAS["port"])
                Log().Log(PR['log_path'], 'send', UASAD, LINE)
            elif metod == 'BYE':
                usuario = respuesta[1].split(':')[1]
                self.Buscar_usuario(usuario)
                if self.UAS == {}:
                    LINE = "SIP/2.0 404 User Not Found\r\n"
                    LINE += 'Via: SIP/2.0/UDP branch=z87ur749ru8e74\r\n\r\n'
                    print("Enviamos: " + LINE)
                    self.wfile.write(bytes(LINE, 'utf-8'))
                    Log().Log(PR['log_path'], 'send', UAC, LINE)
                else:
                    if usuario in self.Envios:
                        cliente = self.Envios[usuario]
                        del self.Envios[usuario]
                        del self.Envios[cliente]
                        print(self.Envios)
                        #Mismo procedimiento que INVITE
                        port = str(self.UAS["port"])
                        ip = self.UAS["address"]
                        self.Conectar_Enviar_Decod(ip, port, line)
                        self.Participantes = []
                    else:
                        sys.exit("User not in conversation")
            else:
                UASAD = self.UAS["address"] + '' + str(self.UAS["port"])
                LINE = "SIP/2.0 400 Bad Request\r\n"
                LINE += 'Via: SIP/2.0/UDP branch=z87ur749ru8e74\r\n\r\n'
                self.wfile.write(bytes(LINE, 'utf-8'))
                print("Enviamos: " + LINE)
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
            fich_json = open(PR['database_path'], 'r')
            self.users_dic = json.load(fich_json)
        except:
            self.users_dic = {}


def IPVal(ip):
    try:
        #Dirección IP válida
        socket.inet_aton(ip)
    except socket.error:
        #Dirección IP no válida
        sys.exit("Not valid IP")


def PORTVal(port):
    try:
        Puerto = int(port)
    except ValueError:
        sys.exit("Port must be integer")
    return Puerto

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
    port = PORTVal(PR['server_puerto'])
    IPVal(PR['server_ip'])
    serv = socketserver.UDPServer(("", port), ProxyRegister)
    # Escribimos inicio log_proxy.txt
    Log().Log(PR['log_path'], 'init/end', ' ', 'Starting...')
    print("Lanzando servidor UDP de eco...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        Log().Log(PR['log_path'], 'init/end', ' ', 'Finishing...')
        sys.exit("Terminado")
