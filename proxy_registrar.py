class ProxyRegister(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    users_dic = {}

    def handle(self):
        caract_dic = {}
        while 1:
            # Leyendo línea a línea lo que nos envía el cliente
            line = self.rfile.read()
            instrucciones_list = line.decode('utf-8').split(' ')
            if instrucciones_list[0] == 'REGISTER':
                self.json2registered()
                usuario = instrucciones_list[1].split(':')[1]
                expires = int(instrucciones_list[2].split(':')[1])
                caract_dic["address"] = self.client_address[0]
                expiration = time.gmtime(int(time.time()) + expires)
                timeexp = time.strftime('%Y-%m-%d %H:%M:%S', expiration)
                caract_dic["expires"] = timeexp
                self.users_dic[usuario] = caract_dic
                if expires == 0:
                    del self.users_dic[usuario]
                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
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
                self.register2json()
            elif :
                self.wfile.write(b"Hemos recibido tu peticion")
                print("El cliente nos manda " + line.decode('utf-8'))
            if not line:
                break

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
